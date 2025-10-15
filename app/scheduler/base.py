"""
Abstract base class for scheduler backends.
"""

from abc import ABC, abstractmethod
from typing import Callable, Any, Optional


class BaseScheduler(ABC):
    """Abstract base class for scheduler implementations."""
    
    @abstractmethod
    def start(self) -> None:
        """Start the scheduler."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        pass
    
    @abstractmethod
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
            func: The function to execute
            job_id: Unique identifier for the job
            trigger: Type of trigger (interval, cron, date)
            **trigger_args: Arguments for the trigger
        """
        pass
    
    @abstractmethod
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler.
        
        Args:
            job_id: Unique identifier for the job
            
        Returns:
            True if job was removed, False if not found
        """
        pass
    
    @abstractmethod
    def update_job(
        self,
        job_id: str,
        **trigger_args
    ) -> bool:
        """
        Update an existing job.
        
        Args:
            job_id: Unique identifier for the job
            **trigger_args: New trigger arguments
            
        Returns:
            True if job was updated, False if not found
        """
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Any]:
        """
        Get a job by ID.
        
        Args:
            job_id: Unique identifier for the job
            
        Returns:
            Job object or None if not found
        """
        pass
    
    @abstractmethod
    def get_jobs(self) -> list:
        """
        Get all jobs.
        
        Returns:
            List of all jobs
        """
        pass

