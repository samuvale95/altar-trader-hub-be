"""
Scheduler factory.

Automatically creates the correct scheduler backend based on configuration.
"""

import logging
from typing import Optional
from app.core.config import settings
from app.scheduler.base import BaseScheduler

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[BaseScheduler] = None


def get_scheduler() -> BaseScheduler:
    """
    Get the scheduler instance.
    
    Creates the scheduler on first call based on SCHEDULER_BACKEND setting.
    Subsequent calls return the same instance.
    
    Returns:
        Scheduler instance (APScheduler or Celery)
    """
    global _scheduler
    
    if _scheduler is None:
        backend = settings.scheduler_backend.lower()
        
        logger.info(f"Initializing scheduler with backend: {backend}")
        
        if backend == "apscheduler":
            from app.scheduler.apscheduler_backend import APSchedulerBackend
            _scheduler = APSchedulerBackend()
            logger.info("Using APScheduler backend")
            
        elif backend == "celery":
            from app.scheduler.celery_backend import CeleryBackend
            _scheduler = CeleryBackend()
            logger.info("Using Celery backend")
            
        else:
            logger.error(f"Unknown scheduler backend: {backend}")
            raise ValueError(
                f"Unknown scheduler backend: {backend}. "
                f"Valid options: 'apscheduler', 'celery'"
            )
    
    return _scheduler


def start_scheduler() -> None:
    """
    Start the scheduler and register default jobs.
    
    This should be called on application startup.
    """
    scheduler = get_scheduler()
    
    try:
        # Start the scheduler
        scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Register default jobs
        _register_default_jobs(scheduler)
        
        # Reload active strategy jobs
        from app.scheduler.manager import reload_active_strategies, reload_data_collection_configs
        strategies_count = reload_active_strategies()
        
        # Reload data collection configs
        configs_count = reload_data_collection_configs()
        
        logger.info(
            f"All scheduler jobs registered: "
            f"{strategies_count} strategies, {configs_count} data collection configs"
        )
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise


def _register_default_jobs(scheduler: BaseScheduler) -> None:
    """
    Register default background jobs.
    
    Args:
        scheduler: Scheduler instance
    """
    from app.scheduler.jobs import (
        collect_crypto_data,
        cleanup_old_data,
        health_check,
        update_exchange_symbols
    )
    
    try:
        # Data collection - every 10 minutes
        scheduler.add_job(
            func=collect_crypto_data,
            job_id="collect_crypto_data",
            trigger="interval",
            minutes=10
        )
        logger.info("Registered job: collect_crypto_data")
        
        # Cleanup old data - daily at 3 AM UTC
        scheduler.add_job(
            func=cleanup_old_data,
            job_id="cleanup_old_data",
            trigger="cron",
            hour=3,
            minute=0
        )
        logger.info("Registered job: cleanup_old_data")
        
        # Health check - every hour
        scheduler.add_job(
            func=health_check,
            job_id="health_check",
            trigger="interval",
            hours=1
        )
        logger.info("Registered job: health_check")
        
        # Update exchange symbols - daily at 1 AM UTC
        scheduler.add_job(
            func=update_exchange_symbols,
            job_id="update_exchange_symbols",
            trigger="cron",
            hour=1,
            minute=0
        )
        logger.info("Registered job: update_exchange_symbols")
        
    except Exception as e:
        logger.error(f"Failed to register default jobs: {e}")
        raise


def shutdown_scheduler(wait: bool = True) -> None:
    """
    Shutdown the scheduler.
    
    This should be called on application shutdown.
    
    Args:
        wait: Wait for running jobs to complete
    """
    global _scheduler
    
    if _scheduler:
        try:
            _scheduler.shutdown()
            logger.info("Scheduler shutdown successfully")
            _scheduler = None
        except Exception as e:
            logger.error(f"Failed to shutdown scheduler: {e}")
            raise

