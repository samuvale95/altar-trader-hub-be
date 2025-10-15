"""
APScheduler backend implementation.

Runs background jobs in the same process as the web application.
Jobs persist in PostgreSQL database.
All jobs run asynchronously to avoid blocking the web application.
"""

import asyncio
import logging
from typing import Callable, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from app.core.config import settings
from app.scheduler.base import BaseScheduler

logger = logging.getLogger(__name__)


def async_job_wrapper(func: Callable) -> Callable:
    """
    Wrapper to run async functions in APScheduler.
    
    APScheduler doesn't natively support async functions,
    so we wrap them to run in the asyncio event loop.
    """
    def wrapper(*args, **kwargs):
        try:
            # Check if function is async
            if asyncio.iscoroutinefunction(func):
                # Run async function in event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(func(*args, **kwargs))
                finally:
                    loop.close()
                return result
            else:
                # Run sync function normally
                return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing job {func.__name__}: {e}", exc_info=True)
            raise
    
    return wrapper


class APSchedulerBackend(BaseScheduler):
    """APScheduler implementation."""
    
    def __init__(self):
        """Initialize APScheduler with PostgreSQL persistence."""
        self.scheduler: Optional[BackgroundScheduler] = None
        self._setup_scheduler()
    
    def _setup_scheduler(self):
        """Configure APScheduler with database persistence."""
        try:
            # Configure job store (PostgreSQL)
            jobstores = {
                'default': SQLAlchemyJobStore(url=settings.database_url)
            }
            
            # Configure executors (thread pool for non-blocking execution)
            executors = {
                'default': ThreadPoolExecutor(max_workers=20)
            }
            
            # Job defaults
            job_defaults = {
                'coalesce': True,  # Combine multiple missed runs into one
                'max_instances': 3,  # Max concurrent instances of same job
                'misfire_grace_time': 60  # Grace period for missed jobs (seconds)
            }
            
            # Create scheduler
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='UTC'
            )
            
            logger.info("APScheduler configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to configure APScheduler: {e}")
            raise
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.scheduler and not self.scheduler.running:
            try:
                self.scheduler.start()
                logger.info("APScheduler started successfully")
            except Exception as e:
                logger.error(f"Failed to start APScheduler: {e}")
                raise
        else:
            logger.warning("APScheduler already running")
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the scheduler.
        
        Args:
            wait: Wait for running jobs to complete
        """
        if self.scheduler and self.scheduler.running:
            try:
                self.scheduler.shutdown(wait=wait)
                logger.info("APScheduler shutdown successfully")
            except Exception as e:
                logger.error(f"Failed to shutdown APScheduler: {e}")
                raise
    
    def add_job(
        self,
        func: Callable,
        job_id: str,
        trigger: str = "interval",
        **trigger_args
    ) -> Any:
        """
        Add a job to the scheduler.
        
        Args:
            func: The function to execute (can be async)
            job_id: Unique identifier for the job
            trigger: Type of trigger (interval, cron, date)
            **trigger_args: Arguments for the trigger
                - For interval: seconds, minutes, hours, days, weeks
                - For cron: year, month, day, week, day_of_week, hour, minute, second
                - For date: run_date
        
        Returns:
            Job object
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        try:
            # Wrap function to handle async execution
            wrapped_func = async_job_wrapper(func)
            
            # Create trigger
            if trigger == "interval":
                trigger_obj = IntervalTrigger(**trigger_args)
            elif trigger == "cron":
                trigger_obj = CronTrigger(**trigger_args)
            elif trigger == "date":
                trigger_obj = DateTrigger(**trigger_args)
            else:
                raise ValueError(f"Unknown trigger type: {trigger}")
            
            # Add job
            job = self.scheduler.add_job(
                func=wrapped_func,
                trigger=trigger_obj,
                id=job_id,
                replace_existing=True,
                name=job_id
            )
            
            logger.info(f"Added job: {job_id} with trigger: {trigger}")
            return job
            
        except Exception as e:
            logger.error(f"Failed to add job {job_id}: {e}")
            raise
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler.
        
        Args:
            job_id: Unique identifier for the job
            
        Returns:
            True if job was removed, False if not found
        """
        if not self.scheduler:
            return False
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {e}")
            return False
    
    def update_job(
        self,
        job_id: str,
        **trigger_args
    ) -> bool:
        """
        Update an existing job's trigger.
        
        Args:
            job_id: Unique identifier for the job
            **trigger_args: New trigger arguments
            
        Returns:
            True if job was updated, False if not found
        """
        if not self.scheduler:
            return False
        
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                logger.warning(f"Job not found: {job_id}")
                return False
            
            # Reschedule job with new trigger
            job.reschedule(
                trigger=IntervalTrigger(**trigger_args)
            )
            
            logger.info(f"Updated job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Any]:
        """
        Get a job by ID.
        
        Args:
            job_id: Unique identifier for the job
            
        Returns:
            Job object or None if not found
        """
        if not self.scheduler:
            return None
        
        return self.scheduler.get_job(job_id)
    
    def get_jobs(self) -> list:
        """
        Get all jobs.
        
        Returns:
            List of all jobs
        """
        if not self.scheduler:
            return []
        
        return self.scheduler.get_jobs()
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        try:
            if self.scheduler:
                self.scheduler.pause_job(job_id)
                logger.info(f"Paused job: {job_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
        return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        try:
            if self.scheduler:
                self.scheduler.resume_job(job_id)
                logger.info(f"Resumed job: {job_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
        return False

