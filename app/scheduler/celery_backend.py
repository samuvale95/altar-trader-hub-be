"""
Celery backend implementation (wrapper).

Uses existing Celery configuration from app.tasks.celery_app.
Requires separate worker dyno to run.
"""

import logging
from typing import Callable, Any, Optional
from app.scheduler.base import BaseScheduler

logger = logging.getLogger(__name__)


class CeleryBackend(BaseScheduler):
    """
    Celery implementation.
    
    Note: This is a wrapper around the existing Celery app.
    Jobs are added to Celery Beat schedule dynamically.
    """
    
    def __init__(self):
        """Initialize Celery backend."""
        try:
            from app.tasks.celery_app import celery_app
            self.celery_app = celery_app
            logger.info("Celery backend initialized")
        except ImportError as e:
            logger.error(f"Failed to import Celery app: {e}")
            raise RuntimeError(
                "Celery is not available. "
                "Make sure Celery is installed and configured."
            )
    
    def start(self) -> None:
        """
        Start the scheduler.
        
        Note: For Celery, the worker must be started separately.
        This method is a no-op for compatibility.
        """
        logger.info("Celery backend: Worker must be started separately")
        logger.info("Run: celery -A app.tasks.celery_app worker --loglevel=info")
    
    def shutdown(self) -> None:
        """
        Shutdown the scheduler.
        
        Note: For Celery, this is handled by the worker process.
        This method is a no-op for compatibility.
        """
        logger.info("Celery backend: Shutdown handled by worker process")
    
    def add_job(
        self,
        func: Callable,
        job_id: str,
        trigger: str = "interval",
        **trigger_args
    ) -> Any:
        """
        Add a job to Celery Beat schedule.
        
        Args:
            func: The function to execute (must be a Celery task)
            job_id: Unique identifier for the job
            trigger: Type of trigger (interval, cron)
            **trigger_args: Arguments for the trigger
        
        Returns:
            Task signature
        """
        try:
            # Convert trigger_args to Celery schedule format
            if trigger == "interval":
                from celery.schedules import schedule
                
                # Extract interval in seconds
                seconds = trigger_args.get('seconds', 0)
                minutes = trigger_args.get('minutes', 0)
                hours = trigger_args.get('hours', 0)
                days = trigger_args.get('days', 0)
                
                total_seconds = seconds + (minutes * 60) + (hours * 3600) + (days * 86400)
                
                # Add to beat schedule
                self.celery_app.conf.beat_schedule[job_id] = {
                    'task': func.__name__ if hasattr(func, '__name__') else str(func),
                    'schedule': schedule(run_every=total_seconds),
                }
                
            elif trigger == "cron":
                from celery.schedules import crontab
                
                # Convert cron args
                cron_schedule = crontab(
                    minute=trigger_args.get('minute', '*'),
                    hour=trigger_args.get('hour', '*'),
                    day_of_week=trigger_args.get('day_of_week', '*'),
                    day_of_month=trigger_args.get('day', '*'),
                    month_of_year=trigger_args.get('month', '*'),
                )
                
                self.celery_app.conf.beat_schedule[job_id] = {
                    'task': func.__name__ if hasattr(func, '__name__') else str(func),
                    'schedule': cron_schedule,
                }
            
            logger.info(f"Added Celery job: {job_id}")
            return func
            
        except Exception as e:
            logger.error(f"Failed to add Celery job {job_id}: {e}")
            raise
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from Celery Beat schedule.
        
        Args:
            job_id: Unique identifier for the job
            
        Returns:
            True if job was removed, False if not found
        """
        try:
            if job_id in self.celery_app.conf.beat_schedule:
                del self.celery_app.conf.beat_schedule[job_id]
                logger.info(f"Removed Celery job: {job_id}")
                return True
            else:
                logger.warning(f"Celery job not found: {job_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to remove Celery job {job_id}: {e}")
            return False
    
    def update_job(
        self,
        job_id: str,
        **trigger_args
    ) -> bool:
        """
        Update an existing Celery job.
        
        Args:
            job_id: Unique identifier for the job
            **trigger_args: New trigger arguments
            
        Returns:
            True if job was updated, False if not found
        """
        try:
            if job_id not in self.celery_app.conf.beat_schedule:
                logger.warning(f"Celery job not found: {job_id}")
                return False
            
            job_config = self.celery_app.conf.beat_schedule[job_id]
            
            # Update interval schedule
            from celery.schedules import schedule
            
            seconds = trigger_args.get('seconds', 0)
            minutes = trigger_args.get('minutes', 0)
            hours = trigger_args.get('hours', 0)
            days = trigger_args.get('days', 0)
            
            total_seconds = seconds + (minutes * 60) + (hours * 3600) + (days * 86400)
            
            job_config['schedule'] = schedule(run_every=total_seconds)
            
            logger.info(f"Updated Celery job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Celery job {job_id}: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Any]:
        """
        Get a job by ID.
        
        Args:
            job_id: Unique identifier for the job
            
        Returns:
            Job config or None if not found
        """
        return self.celery_app.conf.beat_schedule.get(job_id)
    
    def get_jobs(self) -> list:
        """
        Get all jobs.
        
        Returns:
            List of all job configs
        """
        return list(self.celery_app.conf.beat_schedule.items())

