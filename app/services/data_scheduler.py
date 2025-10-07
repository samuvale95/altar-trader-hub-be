"""
Data collection scheduler service.
"""

import asyncio
from datetime import datetime, timedelta
from app.core.logging import get_logger
from app.services.data_feeder import data_feeder
from app.services.symbol_manager import symbol_manager

logger = get_logger(__name__)


class DataScheduler:
    """Service for scheduling data collection tasks."""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_task = None
        self.collection_interval = 300  # 5 minutes
        self.symbol_refresh_interval = 3600  # 1 hour
    
    async def start_scheduler(self):
        """Start the data collection scheduler."""
        
        if self.is_running:
            logger.warning("Data scheduler is already running")
            return
        
        logger.info("Starting data collection scheduler")
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._run_scheduler())
        
        logger.info("Data collection scheduler started")
    
    async def stop_scheduler(self):
        """Stop the data collection scheduler."""
        
        if not self.is_running:
            logger.warning("Data scheduler is not running")
            return
        
        logger.info("Stopping data collection scheduler")
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Data collection scheduler stopped")
    
    async def _run_scheduler(self):
        """Run the scheduler loop."""
        
        last_symbol_refresh = datetime.utcnow()
        last_data_collection = datetime.utcnow()
        
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                # Check if we need to refresh symbols
                if (current_time - last_symbol_refresh).total_seconds() >= self.symbol_refresh_interval:
                    logger.info("Refreshing symbols cache")
                    symbol_manager.refresh_symbols_cache()
                    last_symbol_refresh = current_time
                
                # Check if we need to start data collection
                if (current_time - last_data_collection).total_seconds() >= self.collection_interval:
                    logger.info("Starting scheduled data collection")
                    
                    # Import task manager here to avoid circular imports
                    from app.services.task_manager import task_manager
                    
                    # Check if there's already a data collection task running
                    active_tasks = task_manager.get_active_tasks()
                    data_collection_running = any(
                        task.task_type == "data_collection" for task in active_tasks.values()
                    )
                    
                    if not data_collection_running:
                        # Submit new data collection task
                        task_id = await task_manager.submit_task(
                            "scheduled_data_collection",
                            data_feeder.collect_market_data_async
                        )
                        logger.info(f"Scheduled data collection task submitted: {task_id}")
                    else:
                        logger.info("Data collection already running, skipping scheduled collection")
                    
                    last_data_collection = current_time
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                logger.info("Data scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Error in data scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def get_scheduler_status(self):
        """Get scheduler status."""
        
        # Get task manager status
        from app.services.task_manager import task_manager
        active_tasks = task_manager.get_active_tasks()
        data_collection_running = any(
            task.task_type in ["data_collection", "scheduled_data_collection"] 
            for task in active_tasks.values()
        )
        
        return {
            "is_running": self.is_running,
            "collection_interval": self.collection_interval,
            "symbol_refresh_interval": self.symbol_refresh_interval,
            "data_collection_running": data_collection_running,
            "active_tasks_count": len(active_tasks),
            "scheduler_task_types": list(set(task.task_type for task in active_tasks.values()))
        }


# Global scheduler instance
data_scheduler = DataScheduler()

