"""
Task manager for handling background operations.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Task information model."""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    total: int = 100
    message: str = ""
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class TaskManager:
    """Manager for background tasks."""
    
    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._task_info: Dict[str, TaskInfo] = {}
        self._max_concurrent_tasks = 5
    
    async def submit_task(
        self,
        task_type: str,
        coro: Callable,
        *args,
        **kwargs
    ) -> str:
        """Submit a new background task."""
        
        task_id = str(uuid.uuid4())
        
        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        self._task_info[task_id] = task_info
        
        # Create and store the actual task
        task = asyncio.create_task(
            self._execute_task(task_id, coro, *args, **kwargs)
        )
        
        self._tasks[task_id] = task
        
        logger.info("Task submitted", task_id=task_id, task_type=task_type)
        
        return task_id
    
    async def _execute_task(
        self,
        task_id: str,
        coro: Callable,
        *args,
        **kwargs
    ) -> None:
        """Execute a task and update its status."""
        
        task_info = self._task_info[task_id]
        
        try:
            # Update status to running
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = datetime.utcnow()
            task_info.message = "Task started"
            
            logger.info("Task started", task_id=task_id, task_type=task_info.task_type)
            
            # Execute the coroutine
            result = await coro(*args, **kwargs)
            
            # Update status to completed
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.utcnow()
            task_info.progress = 100
            task_info.message = "Task completed successfully"
            task_info.result = result
            
            logger.info("Task completed", task_id=task_id, task_type=task_info.task_type)
            
        except Exception as e:
            # Update status to failed
            task_info.status = TaskStatus.FAILED
            task_info.completed_at = datetime.utcnow()
            task_info.message = f"Task failed: {str(e)}"
            task_info.error = str(e)
            
            logger.error("Task failed", task_id=task_id, task_type=task_info.task_type, error=str(e))
            
        finally:
            # Clean up task reference after a delay
            asyncio.create_task(self._cleanup_task(task_id))
    
    async def _cleanup_task(self, task_id: str, delay: int = 300) -> None:
        """Clean up completed task after delay."""
        
        await asyncio.sleep(delay)
        
        if task_id in self._tasks:
            del self._tasks[task_id]
        
        if task_id in self._task_info:
            task_info = self._task_info[task_id]
            if task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                del self._task_info[task_id]
                logger.info("Task cleaned up", task_id=task_id)
    
    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """Get task status by ID."""
        
        return self._task_info.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, TaskInfo]:
        """Get all task information."""
        
        return self._task_info.copy()
    
    def get_tasks_by_type(self, task_type: str) -> Dict[str, TaskInfo]:
        """Get tasks by type."""
        
        return {
            task_id: task_info
            for task_id, task_info in self._task_info.items()
            if task_info.task_type == task_type
        }
    
    def get_active_tasks(self) -> Dict[str, TaskInfo]:
        """Get all active tasks."""
        
        return {
            task_id: task_info
            for task_id, task_info in self._task_info.items()
            if task_info.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        
        if task_id not in self._tasks:
            return False
        
        task = self._tasks[task_id]
        
        if task.done():
            return False
        
        # Cancel the task
        task.cancel()
        
        # Update task info
        if task_id in self._task_info:
            task_info = self._task_info[task_id]
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.utcnow()
            task_info.message = "Task cancelled"
        
        logger.info("Task cancelled", task_id=task_id)
        
        return True
    
    async def update_task_progress(
        self,
        task_id: str,
        progress: int,
        message: str = "",
        total: Optional[int] = None
    ) -> bool:
        """Update task progress."""
        
        if task_id not in self._task_info:
            return False
        
        task_info = self._task_info[task_id]
        
        task_info.progress = min(progress, 100)
        if message:
            task_info.message = message
        if total is not None:
            task_info.total = total
        
        return True
    
    def get_task_count(self) -> Dict[str, int]:
        """Get task count by status."""
        
        counts = {}
        for status in TaskStatus:
            counts[status.value] = sum(
                1 for task_info in self._task_info.values()
                if task_info.status == status
            )
        
        return counts
    
    async def shutdown(self) -> None:
        """Shutdown task manager and cancel all running tasks."""
        
        logger.info("Shutting down task manager")
        
        # Cancel all running tasks
        for task_id, task in self._tasks.items():
            if not task.done():
                task.cancel()
                
                # Update task info
                if task_id in self._task_info:
                    task_info = self._task_info[task_id]
                    task_info.status = TaskStatus.CANCELLED
                    task_info.completed_at = datetime.utcnow()
                    task_info.message = "Task cancelled during shutdown"
        
        # Wait for all tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        
        logger.info("Task manager shutdown completed")


# Global task manager instance
task_manager = TaskManager()

