"""
Cleanup and maintenance tasks.
"""

from celery import current_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.tasks.celery_app import celery_app
from app.models.market_data import MarketData, News, Indicator
from app.models.order import Order, Trade
from app.models.strategy import StrategySignal
from app.models.notification import Notification
from datetime import datetime, timedelta

logger = get_logger(__name__)


@celery_app.task(bind=True)
def cleanup_old_data(self):
    """Clean up old data to maintain database performance."""
    
    db = SessionLocal()
    
    try:
        logger.info("Starting data cleanup")
        
        # Clean up old market data (keep last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Delete old market data
        old_market_data = db.query(MarketData).filter(
            MarketData.timestamp < cutoff_date
        ).count()
        
        if old_market_data > 0:
            db.query(MarketData).filter(
                MarketData.timestamp < cutoff_date
            ).delete()
            
            logger.info("Deleted old market data", count=old_market_data)
        
        # Clean up old indicators (keep last 30 days)
        old_indicators = db.query(Indicator).filter(
            Indicator.timestamp < cutoff_date
        ).count()
        
        if old_indicators > 0:
            db.query(Indicator).filter(
                Indicator.timestamp < cutoff_date
            ).delete()
            
            logger.info("Deleted old indicators", count=old_indicators)
        
        # Clean up old news (keep last 90 days)
        news_cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_news = db.query(News).filter(
            News.published_at < news_cutoff_date
        ).count()
        
        if old_news > 0:
            db.query(News).filter(
                News.published_at < news_cutoff_date
            ).delete()
            
            logger.info("Deleted old news", count=old_news)
        
        # Clean up old strategy signals (keep last 30 days)
        old_signals = db.query(StrategySignal).filter(
            StrategySignal.timestamp < cutoff_date
        ).count()
        
        if old_signals > 0:
            db.query(StrategySignal).filter(
                StrategySignal.timestamp < cutoff_date
            ).delete()
            
            logger.info("Deleted old strategy signals", count=old_signals)
        
        # Clean up old notifications (keep last 30 days)
        old_notifications = db.query(Notification).filter(
            Notification.created_at < cutoff_date,
            Notification.status.in_(["sent", "failed"])
        ).count()
        
        if old_notifications > 0:
            db.query(Notification).filter(
                Notification.created_at < cutoff_date,
                Notification.status.in_(["sent", "failed"])
            ).delete()
            
            logger.info("Deleted old notifications", count=old_notifications)
        
        db.commit()
        logger.info("Data cleanup completed")
        
    except Exception as e:
        logger.error("Data cleanup failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def cleanup_failed_orders(self):
    """Clean up failed orders and update their status."""
    
    db = SessionLocal()
    
    try:
        logger.info("Starting failed orders cleanup")
        
        # Find orders that have been pending for too long (1 hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        failed_orders = db.query(Order).filter(
            Order.status == "pending",
            Order.created_at < cutoff_time
        ).all()
        
        for order in failed_orders:
            order.status = "expired"
            order.cancelled_at = datetime.utcnow()
            
            logger.info("Marked order as expired", order_id=order.id)
        
        db.commit()
        logger.info("Failed orders cleanup completed", count=len(failed_orders))
        
    except Exception as e:
        logger.error("Failed orders cleanup failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def cleanup_inactive_strategies(self):
    """Clean up inactive strategies and their data."""
    
    db = SessionLocal()
    
    try:
        logger.info("Starting inactive strategies cleanup")
        
        # Find strategies that have been inactive for more than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        inactive_strategies = db.query(Strategy).filter(
            Strategy.is_active == False,
            Strategy.stopped_at < cutoff_date
        ).all()
        
        for strategy in inactive_strategies:
            # Delete strategy signals
            db.query(StrategySignal).filter(
                StrategySignal.strategy_id == strategy.id
            ).delete()
            
            # Delete strategy performance data
            db.query(StrategyPerformance).filter(
                StrategyPerformance.strategy_id == strategy.id
            ).delete()
            
            # Delete the strategy
            db.delete(strategy)
            
            logger.info("Deleted inactive strategy", strategy_id=strategy.id)
        
        db.commit()
        logger.info("Inactive strategies cleanup completed", count=len(inactive_strategies))
        
    except Exception as e:
        logger.error("Inactive strategies cleanup failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def optimize_database(self):
    """Optimize database performance."""
    
    db = SessionLocal()
    
    try:
        logger.info("Starting database optimization")
        
        # Analyze tables for better query planning
        tables = [
            "market_data",
            "indicators", 
            "orders",
            "trades",
            "strategy_signals",
            "notifications"
        ]
        
        for table in tables:
            try:
                db.execute(f"ANALYZE {table}")
                logger.info("Analyzed table", table=table)
            except Exception as e:
                logger.warning("Failed to analyze table", table=table, error=str(e))
        
        # Update table statistics
        db.execute("UPDATE pg_stat_user_tables SET n_tup_ins = 0, n_tup_upd = 0, n_tup_del = 0")
        
        logger.info("Database optimization completed")
        
    except Exception as e:
        logger.error("Database optimization failed", error=str(e))
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def health_check(self):
    """Perform system health check."""
    
    db = SessionLocal()
    
    try:
        logger.info("Starting health check")
        
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": "healthy",
            "redis": "healthy",
            "celery": "healthy",
            "issues": []
        }
        
        # Check database connection
        try:
            db.execute("SELECT 1")
        except Exception as e:
            health_status["database"] = "unhealthy"
            health_status["issues"].append(f"Database connection failed: {str(e)}")
        
        # Check Redis connection
        try:
            from app.core.database import get_redis
            redis_client = get_redis()
            redis_client.ping()
        except Exception as e:
            health_status["redis"] = "unhealthy"
            health_status["issues"].append(f"Redis connection failed: {str(e)}")
        
        # Check Celery workers
        try:
            from app.tasks.celery_app import celery_app
            stats = celery_app.control.stats()
            if not stats:
                health_status["celery"] = "unhealthy"
                health_status["issues"].append("No Celery workers available")
        except Exception as e:
            health_status["celery"] = "unhealthy"
            health_status["issues"].append(f"Celery check failed: {str(e)}")
        
        # Log health status
        if health_status["issues"]:
            logger.warning("Health check found issues", issues=health_status["issues"])
        else:
            logger.info("Health check passed")
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise
    finally:
        db.close()
