"""
Strategy and data collection job manager.

Manages dynamic scheduling of:
- Trading strategies
- Data collection configurations

Jobs can be started/stopped/updated via API.
"""

import logging
from typing import Optional
from datetime import datetime
from app.scheduler.factory import get_scheduler
from app.scheduler.jobs import execute_single_strategy

logger = logging.getLogger(__name__)


def add_strategy_job(
    strategy_id: int,
    interval_seconds: int,
    start_immediately: bool = False
) -> bool:
    """
    Add a strategy execution job to the scheduler.
    
    Args:
        strategy_id: ID of the strategy
        interval_seconds: Execution interval in seconds
        start_immediately: Execute immediately on addition
        
    Returns:
        True if job was added successfully
    """
    try:
        scheduler = get_scheduler()
        job_id = f"strategy_{strategy_id}"
        
        # Create wrapped function with strategy_id
        async def strategy_wrapper():
            await execute_single_strategy(strategy_id)
        
        # Add job to scheduler
        scheduler.add_job(
            func=strategy_wrapper,
            job_id=job_id,
            trigger="interval",
            seconds=interval_seconds
        )
        
        logger.info(
            f"Added strategy job: {job_id} "
            f"(interval: {interval_seconds}s)"
        )
        
        # Execute immediately if requested
        if start_immediately:
            try:
                import asyncio
                asyncio.create_task(execute_single_strategy(strategy_id))
                logger.info(f"Triggered immediate execution for strategy {strategy_id}")
            except Exception as e:
                logger.warning(f"Failed to execute strategy immediately: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to add strategy job {strategy_id}: {e}")
        return False


def remove_strategy_job(strategy_id: int) -> bool:
    """
    Remove a strategy execution job from the scheduler.
    
    Args:
        strategy_id: ID of the strategy
        
    Returns:
        True if job was removed successfully
    """
    try:
        scheduler = get_scheduler()
        job_id = f"strategy_{strategy_id}"
        
        success = scheduler.remove_job(job_id)
        
        if success:
            logger.info(f"Removed strategy job: {job_id}")
        else:
            logger.warning(f"Strategy job not found: {job_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to remove strategy job {strategy_id}: {e}")
        return False


def update_strategy_job(
    strategy_id: int,
    interval_seconds: int
) -> bool:
    """
    Update a strategy execution job's interval.
    
    Args:
        strategy_id: ID of the strategy
        interval_seconds: New execution interval in seconds
        
    Returns:
        True if job was updated successfully
    """
    try:
        scheduler = get_scheduler()
        job_id = f"strategy_{strategy_id}"
        
        # Check if job exists
        job = scheduler.get_job(job_id)
        if not job:
            logger.warning(f"Strategy job not found: {job_id}")
            # Add as new job
            return add_strategy_job(strategy_id, interval_seconds)
        
        # Update existing job
        success = scheduler.update_job(
            job_id=job_id,
            seconds=interval_seconds
        )
        
        if success:
            logger.info(
                f"Updated strategy job: {job_id} "
                f"(new interval: {interval_seconds}s)"
            )
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to update strategy job {strategy_id}: {e}")
        return False


def pause_strategy_job(strategy_id: int) -> bool:
    """
    Pause a strategy execution job.
    
    Args:
        strategy_id: ID of the strategy
        
    Returns:
        True if job was paused successfully
    """
    try:
        scheduler = get_scheduler()
        job_id = f"strategy_{strategy_id}"
        
        # APScheduler supports pause, Celery doesn't
        if hasattr(scheduler, 'pause_job'):
            success = scheduler.pause_job(job_id)
            if success:
                logger.info(f"Paused strategy job: {job_id}")
            return success
        else:
            # For Celery, just remove the job
            logger.info("Celery backend doesn't support pause, removing job instead")
            return remove_strategy_job(strategy_id)
        
    except Exception as e:
        logger.error(f"Failed to pause strategy job {strategy_id}: {e}")
        return False


def resume_strategy_job(strategy_id: int) -> bool:
    """
    Resume a paused strategy execution job.
    
    Args:
        strategy_id: ID of the strategy
        
    Returns:
        True if job was resumed successfully
    """
    try:
        scheduler = get_scheduler()
        job_id = f"strategy_{strategy_id}"
        
        # APScheduler supports resume, Celery doesn't
        if hasattr(scheduler, 'resume_job'):
            success = scheduler.resume_job(job_id)
            if success:
                logger.info(f"Resumed strategy job: {job_id}")
            return success
        else:
            logger.warning("Celery backend doesn't support resume")
            return False
        
    except Exception as e:
        logger.error(f"Failed to resume strategy job {strategy_id}: {e}")
        return False


def get_strategy_job_status(strategy_id: int) -> Optional[dict]:
    """
    Get status of a strategy job.
    
    Args:
        strategy_id: ID of the strategy
        
    Returns:
        Job status dict or None if not found
    """
    try:
        scheduler = get_scheduler()
        job_id = f"strategy_{strategy_id}"
        
        job = scheduler.get_job(job_id)
        
        if job:
            return {
                "strategy_id": strategy_id,
                "job_id": job_id,
                "active": True,
                "next_run": str(job.next_run_time) if hasattr(job, 'next_run_time') else None,
            }
        else:
            return {
                "strategy_id": strategy_id,
                "job_id": job_id,
                "active": False,
                "next_run": None,
            }
        
    except Exception as e:
        logger.error(f"Failed to get strategy job status {strategy_id}: {e}")
        return None


def reload_active_strategies() -> int:
    """
    Reload all active strategies from database.
    
    This is called on application startup to restore
    scheduled jobs from the database.
    
    Returns:
        Number of strategies reloaded
    """
    logger.info("Reloading active strategies from database...")
    
    try:
        from app.core.database import SessionLocal
        from app.models.strategy import Strategy
        
        db = SessionLocal()
        try:
            # Get all active strategies
            active_strategies = db.query(Strategy).filter(
                Strategy.is_active == True
            ).all()
            
            count = 0
            for strategy in active_strategies:
                # Add job for each active strategy
                success = add_strategy_job(
                    strategy_id=strategy.id,
                    interval_seconds=strategy.execution_interval,
                    start_immediately=False
                )
                
                if success:
                    count += 1
            
            logger.info(f"Reloaded {count} active strategies")
            return count
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to reload active strategies: {e}")
        return 0


def get_all_strategy_jobs() -> list:
    """
    Get all strategy jobs currently scheduled.
    
    Returns:
        List of job information dicts
    """
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        # Filter only strategy jobs
        strategy_jobs = [
            {
                "job_id": job.id,
                "strategy_id": int(job.id.replace("strategy_", "")),
                "next_run": str(job.next_run_time) if hasattr(job, 'next_run_time') else None,
            }
            for job in jobs
            if job.id.startswith("strategy_")
        ]
        
        return strategy_jobs
        
    except Exception as e:
        logger.error(f"Failed to get strategy jobs: {e}")
        return []


# ============================================================================
# Data Collection Job Management
# ============================================================================

def add_data_collection_job(config_id: int) -> bool:
    """
    Add a data collection job to the scheduler based on DB config.
    
    Args:
        config_id: ID of DataCollectionConfig
        
    Returns:
        True if job was added successfully
    """
    try:
        from app.core.database import SessionLocal
        from app.models.data_collection import DataCollectionConfig
        from app.scheduler.jobs import collect_data_for_config
        
        db = SessionLocal()
        try:
            config = db.query(DataCollectionConfig).get(config_id)
            if not config:
                logger.error(f"Data collection config {config_id} not found")
                return False
            
            scheduler = get_scheduler()
            job_id = f"collect_data_{config_id}"
            
            # Create wrapped function with config_id
            async def data_collection_wrapper():
                await collect_data_for_config(config_id)
            
            # Add job to scheduler
            scheduler.add_job(
                func=data_collection_wrapper,
                job_id=job_id,
                trigger="interval",
                minutes=config.interval_minutes
            )
            
            # Update job_id in config
            config.job_id = job_id
            db.commit()
            
            logger.info(
                f"Added data collection job: {job_id} "
                f"for {config.symbol} on {config.exchange} "
                f"(interval: {config.interval_minutes}min)"
            )
            
            return True
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to add data collection job {config_id}: {e}")
        return False


def remove_data_collection_job(config_id: int) -> bool:
    """
    Remove a data collection job from the scheduler.
    
    Args:
        config_id: ID of DataCollectionConfig
        
    Returns:
        True if job was removed successfully
    """
    try:
        scheduler = get_scheduler()
        job_id = f"collect_data_{config_id}"
        
        success = scheduler.remove_job(job_id)
        
        if success:
            logger.info(f"Removed data collection job: {job_id}")
        else:
            logger.warning(f"Data collection job not found: {job_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to remove data collection job {config_id}: {e}")
        return False


def update_data_collection_job(config_id: int) -> bool:
    """
    Update a data collection job's interval.
    
    Args:
        config_id: ID of DataCollectionConfig
        
    Returns:
        True if job was updated successfully
    """
    try:
        from app.core.database import SessionLocal
        from app.models.data_collection import DataCollectionConfig
        
        db = SessionLocal()
        try:
            config = db.query(DataCollectionConfig).get(config_id)
            if not config:
                logger.error(f"Data collection config {config_id} not found")
                return False
            
            scheduler = get_scheduler()
            job_id = f"collect_data_{config_id}"
            
            # Update existing job
            success = scheduler.update_job(
                job_id=job_id,
                minutes=config.interval_minutes
            )
            
            if success:
                logger.info(
                    f"Updated data collection job: {job_id} "
                    f"(new interval: {config.interval_minutes}min)"
                )
            else:
                # If update failed, try to add as new job
                logger.warning(f"Job {job_id} not found, creating new one")
                return add_data_collection_job(config_id)
            
            return success
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to update data collection job {config_id}: {e}")
        return False


async def trigger_data_collection_now(config_id: int) -> None:
    """
    Trigger data collection immediately for a config.
    
    Args:
        config_id: ID of DataCollectionConfig
    """
    try:
        from app.scheduler.jobs import collect_data_for_config
        await collect_data_for_config(config_id)
        logger.info(f"Manually triggered data collection for config {config_id}")
    except Exception as e:
        logger.error(f"Failed to trigger data collection for config {config_id}: {e}")


def reload_data_collection_configs() -> int:
    """
    Reload all enabled data collection configs from database.
    
    Called on application startup to restore scheduled jobs.
    
    Returns:
        Number of configs reloaded
    """
    logger.info("Reloading data collection configs from database...")
    
    try:
        from app.core.database import SessionLocal
        from app.models.data_collection import DataCollectionConfig
        
        db = SessionLocal()
        try:
            # Get all enabled configs
            enabled_configs = db.query(DataCollectionConfig).filter(
                DataCollectionConfig.enabled == True
            ).all()
            
            count = 0
            for config in enabled_configs:
                success = add_data_collection_job(config.id)
                if success:
                    count += 1
            
            logger.info(f"Reloaded {count} data collection configs")
            return count
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to reload data collection configs: {e}")
        return 0

