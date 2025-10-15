"""
Background jobs (async).

All jobs are async to avoid blocking the web application.
These jobs are automatically registered by the scheduler on startup.
"""

import logging
from datetime import datetime, timedelta
from typing import List
import asyncio

logger = logging.getLogger(__name__)


async def collect_crypto_data() -> None:
    """
    Collect cryptocurrency market data from exchanges.
    
    Runs every 10 minutes by default.
    This is an async job that won't block the web application.
    """
    logger.info("Starting crypto data collection...")
    
    try:
        from app.core.database import SessionLocal
        from app.services.data_collector import DataCollectorService
        
        db = SessionLocal()
        try:
            collector = DataCollectorService(db)
            
            # Major trading pairs to collect
            symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
            timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
            
            # Collect data for each symbol concurrently
            tasks = []
            for symbol in symbols:
                for timeframe in timeframes:
                    task = collector.collect_market_data(
                        exchange='binance',
                        symbol=symbol,
                        timeframe=timeframe
                    )
                    tasks.append(task)
            
            # Run all collections concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successes and failures
            successes = sum(1 for r in results if not isinstance(r, Exception))
            failures = sum(1 for r in results if isinstance(r, Exception))
            
            logger.info(
                f"Crypto data collection completed: "
                f"{successes} succeeded, {failures} failed"
            )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in collect_crypto_data: {e}", exc_info=True)
        raise


async def cleanup_old_data() -> None:
    """
    Clean up old market data to save database space.
    
    Runs daily at 3 AM UTC.
    Removes data older than 30 days.
    """
    logger.info("Starting data cleanup...")
    
    try:
        from app.core.database import SessionLocal
        from app.models.market_data import MarketData
        from sqlalchemy import delete
        
        db = SessionLocal()
        try:
            # Delete data older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            stmt = delete(MarketData).where(MarketData.timestamp < cutoff_date)
            result = db.execute(stmt)
            db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} old market data records")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in cleanup_old_data: {e}", exc_info=True)
        raise


async def execute_strategies() -> None:
    """
    Execute all active trading strategies.
    
    This is called for individual strategies by the strategy manager.
    Not registered as a default job.
    """
    logger.info("Starting strategy execution...")
    
    try:
        from app.core.database import SessionLocal
        from app.models.strategy import Strategy
        from app.services.strategy_executor import StrategyExecutor
        
        db = SessionLocal()
        try:
            # Get all active strategies
            active_strategies = db.query(Strategy).filter(
                Strategy.is_active == True
            ).all()
            
            if not active_strategies:
                logger.info("No active strategies to execute")
                return
            
            executor = StrategyExecutor(db)
            
            # Execute strategies concurrently
            tasks = [
                executor.execute_strategy(strategy.id)
                for strategy in active_strategies
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successes = sum(1 for r in results if not isinstance(r, Exception))
            failures = sum(1 for r in results if isinstance(r, Exception))
            
            logger.info(
                f"Strategy execution completed: "
                f"{successes} succeeded, {failures} failed"
            )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in execute_strategies: {e}", exc_info=True)
        raise


async def health_check() -> None:
    """
    Perform system health check.
    
    Runs every hour.
    Checks database, Redis, and system health.
    """
    logger.info("Starting health check...")
    
    try:
        from app.core.database import engine, redis_client
        
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": "healthy",
            "redis": "healthy" if redis_client else "not_configured",
            "scheduler": "healthy",
            "issues": []
        }
        
        # Check database connection
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
        except Exception as e:
            health_status["database"] = "unhealthy"
            health_status["issues"].append(f"Database: {str(e)}")
        
        # Check Redis connection (if configured)
        if redis_client:
            try:
                redis_client.ping()
            except Exception as e:
                health_status["redis"] = "unhealthy"
                health_status["issues"].append(f"Redis: {str(e)}")
        
        # Log health status
        if health_status["issues"]:
            logger.warning(f"Health check issues found: {health_status['issues']}")
        else:
            logger.info("Health check passed - all systems operational")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in health_check: {e}", exc_info=True)
        raise


async def update_exchange_symbols() -> None:
    """
    Update available trading symbols from exchanges.
    
    Runs daily at 1 AM UTC.
    Fetches and caches available symbols from all exchanges.
    """
    logger.info("Starting exchange symbols update...")
    
    try:
        from app.services.exchange_service import ExchangeService
        
        exchange_service = ExchangeService()
        exchanges = ['binance', 'kraken', 'kucoin']
        
        # Update symbols for each exchange concurrently
        tasks = [
            exchange_service.get_available_symbols(exchange_name)
            for exchange_name in exchanges
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        for exchange_name, result in zip(exchanges, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to update symbols for {exchange_name}: {result}")
            else:
                logger.info(f"Updated {len(result)} symbols for {exchange_name}")
        
        logger.info("Exchange symbols update completed")
        
    except Exception as e:
        logger.error(f"Error in update_exchange_symbols: {e}", exc_info=True)
        raise


async def sync_user_balances() -> None:
    """
    Synchronize user balances from exchanges.
    
    Updates portfolio balances for all users with connected exchange accounts.
    """
    logger.info("Starting user balance sync...")
    
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.services.portfolio_service import PortfolioService
        
        db = SessionLocal()
        try:
            # Get users with exchange API keys configured
            users = db.query(User).filter(
                User.is_active == True
            ).all()
            
            # Sync balances concurrently
            tasks = []
            for user in users:
                portfolio_service = PortfolioService(db)
                task = portfolio_service.sync_balances(user.id)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successes = sum(1 for r in results if not isinstance(r, Exception))
            failures = sum(1 for r in results if isinstance(r, Exception))
            
            logger.info(
                f"Balance sync completed: "
                f"{successes} succeeded, {failures} failed"
            )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in sync_user_balances: {e}", exc_info=True)
        raise


# Individual strategy execution (called by manager)
async def execute_single_strategy(strategy_id: int) -> None:
    """
    Execute a single trading strategy.
    
    This is called by the strategy manager for each active strategy.
    
    Args:
        strategy_id: ID of the strategy to execute
    """
    logger.info(f"Executing strategy {strategy_id}...")
    
    try:
        from app.core.database import SessionLocal
        from app.services.strategy_executor import StrategyExecutor
        
        db = SessionLocal()
        try:
            executor = StrategyExecutor(db)
            await executor.execute_strategy(strategy_id)
            
            logger.info(f"Strategy {strategy_id} executed successfully")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error executing strategy {strategy_id}: {e}", exc_info=True)
        raise


async def collect_data_for_config(config_id: int) -> None:
    """
    Collect data based on a DataCollectionConfig.
    
    This function:
    1. Creates a JobExecutionLog entry (started)
    2. Collects data for all configured timeframes
    3. Updates JobExecutionLog with results (finished)
    
    Args:
        config_id: ID of the DataCollectionConfig
    """
    from app.core.database import SessionLocal
    from app.models.data_collection import DataCollectionConfig, JobExecutionLog
    from app.services.data_collector import DataCollectorService
    
    db = SessionLocal()
    log_entry = None
    
    try:
        # Get config
        config = db.query(DataCollectionConfig).get(config_id)
        if not config:
            logger.error(f"Data collection config {config_id} not found")
            return
        
        if not config.enabled:
            logger.info(f"Config {config_id} is disabled, skipping")
            return
        
        # Create log entry (started)
        log_entry = JobExecutionLog(
            job_name=f"collect_data_{config_id}",
            job_type="data_collection",
            symbol=config.symbol,
            exchange=config.exchange,
            started_at=datetime.utcnow(),
            status="running"
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        logger.info(
            f"Starting data collection for {config.symbol} on {config.exchange} "
            f"(log_id: {log_entry.id})"
        )
        
        # Collect data for each timeframe
        collector = DataCollectorService(db)
        total_records = 0
        
        tasks = []
        for timeframe in config.timeframes:
            task = collector.collect_market_data(
                exchange=config.exchange,
                symbol=config.symbol,
                timeframe=timeframe
            )
            tasks.append(task)
        
        # Execute all timeframes concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error collecting data: {result}")
            else:
                total_records += 1  # Could be number of candles collected
        
        # Update log entry (success)
        finished_at = datetime.utcnow()
        duration = (finished_at - log_entry.started_at).total_seconds()
        
        log_entry.finished_at = finished_at
        log_entry.duration_seconds = duration
        log_entry.status = "success"
        log_entry.records_collected = total_records
        log_entry.metadata = {
            "timeframes_collected": len([r for r in results if not isinstance(r, Exception)]),
            "timeframes_failed": len([r for r in results if isinstance(r, Exception)]),
            "timeframes": config.timeframes
        }
        
        db.commit()
        
        logger.info(
            f"Data collection completed for {config.symbol}: "
            f"{total_records} records in {duration:.2f}s "
            f"(log_id: {log_entry.id})"
        )
        
    except Exception as e:
        logger.error(f"Error in collect_data_for_config {config_id}: {e}", exc_info=True)
        
        # Update log entry (failed)
        if log_entry:
            try:
                finished_at = datetime.utcnow()
                duration = (finished_at - log_entry.started_at).total_seconds()
                
                log_entry.finished_at = finished_at
                log_entry.duration_seconds = duration
                log_entry.status = "failed"
                log_entry.error_message = str(e)
                log_entry.error_type = type(e).__name__
                
                db.commit()
            except Exception as log_error:
                logger.error(f"Failed to update log entry: {log_error}")
        
        raise
        
    finally:
        db.close()

