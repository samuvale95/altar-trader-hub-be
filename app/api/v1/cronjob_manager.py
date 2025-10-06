"""
API endpoints for managing crypto data collection cronjobs.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.core.logging import get_logger
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import threading
import time

router = APIRouter()
logger = get_logger(__name__)

# Global state for cronjob management
cronjob_state = {
    "is_running": False,
    "tasks": {},
    "config": {
        "main_symbols": [
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "XRPUSDT",
            "SOLUSDT", "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT"
        ],
        "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
        "intervals": {
            "main_collection": 30,  # seconds
            "high_volume": 300,     # 5 minutes
            "symbol_update": 1800,  # 30 minutes
            "status_report": 600    # 10 minutes
        }
    },
    "statistics": {
        "total_executions": 0,
        "last_execution": None,
        "success_count": 0,
        "error_count": 0,
        "start_time": None
    }
}

# Background task references
background_tasks = {}

class CronjobConfig(BaseModel):
    """Cronjob configuration model."""
    main_symbols: List[str]
    timeframes: List[str]
    intervals: Dict[str, int]

class CronjobStatus(BaseModel):
    """Cronjob status model."""
    is_running: bool
    config: Dict[str, Any]
    statistics: Dict[str, Any]
    active_tasks: List[str]

class TaskExecution(BaseModel):
    """Task execution model."""
    task_name: str
    status: str  # "success", "error", "running"
    timestamp: datetime
    duration: Optional[float] = None
    error_message: Optional[str] = None

@router.get("/status", response_model=CronjobStatus)
async def get_cronjob_status(current_user: User = Depends(get_current_user)):
    """Get current cronjob status and configuration."""
    
    return CronjobStatus(
        is_running=cronjob_state["is_running"],
        config=cronjob_state["config"],
        statistics=cronjob_state["statistics"],
        active_tasks=list(cronjob_state["tasks"].keys())
    )

@router.post("/start")
async def start_cronjob(
    background_tasks: BackgroundTasks,
    config: Optional[CronjobConfig] = None,
    current_user: User = Depends(get_current_user)
):
    """Start the crypto data collection cronjob."""
    
    if cronjob_state["is_running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cronjob is already running"
        )
    
    # Update configuration if provided
    if config:
        cronjob_state["config"].update(config.dict())
    
    # Start the cronjob
    background_tasks.add_task(run_cronjob)
    
    cronjob_state["is_running"] = True
    cronjob_state["statistics"]["start_time"] = datetime.now()
    
    logger.info("Cronjob started by user: %s", current_user.email)
    
    return {
        "message": "Cronjob started successfully",
        "config": cronjob_state["config"],
        "start_time": cronjob_state["statistics"]["start_time"]
    }

@router.post("/stop")
async def stop_cronjob(current_user: User = Depends(get_current_user)):
    """Stop the crypto data collection cronjob."""
    
    if not cronjob_state["is_running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cronjob is not running"
        )
    
    # Stop all tasks
    for task_name, task in cronjob_state["tasks"].items():
        if task and not task.done():
            task.cancel()
    
    cronjob_state["is_running"] = False
    cronjob_state["tasks"] = {}
    
    logger.info("Cronjob stopped by user: %s", current_user.email)
    
    return {"message": "Cronjob stopped successfully"}

@router.put("/config")
async def update_cronjob_config(
    config: CronjobConfig,
    current_user: User = Depends(get_current_user)
):
    """Update cronjob configuration."""
    
    # Validate configuration
    if not config.main_symbols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one symbol must be specified"
        )
    
    if not config.timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one timeframe must be specified"
        )
    
    # Update configuration
    cronjob_state["config"]["main_symbols"] = config.main_symbols
    cronjob_state["config"]["timeframes"] = config.timeframes
    cronjob_state["config"]["intervals"].update(config.intervals)
    
    logger.info("Cronjob configuration updated by user: %s", current_user.email)
    
    return {
        "message": "Configuration updated successfully",
        "config": cronjob_state["config"]
    }

@router.post("/add-symbols")
async def add_symbols(
    symbols: List[str],
    current_user: User = Depends(get_current_user)
):
    """Add symbols to the cronjob configuration."""
    
    if not symbols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No symbols provided"
        )
    
    # Add new symbols (avoid duplicates)
    current_symbols = set(cronjob_state["config"]["main_symbols"])
    new_symbols = [s.upper() for s in symbols if s.upper() not in current_symbols]
    
    cronjob_state["config"]["main_symbols"].extend(new_symbols)
    
    logger.info("Added %d new symbols by user: %s", len(new_symbols), current_user.email)
    
    return {
        "message": f"Added {len(new_symbols)} new symbols",
        "added_symbols": new_symbols,
        "total_symbols": len(cronjob_state["config"]["main_symbols"])
    }

@router.delete("/remove-symbols")
async def remove_symbols(
    symbols: List[str],
    current_user: User = Depends(get_current_user)
):
    """Remove symbols from the cronjob configuration."""
    
    if not symbols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No symbols provided"
        )
    
    # Remove symbols
    symbols_to_remove = [s.upper() for s in symbols]
    original_count = len(cronjob_state["config"]["main_symbols"])
    
    cronjob_state["config"]["main_symbols"] = [
        s for s in cronjob_state["config"]["main_symbols"]
        if s not in symbols_to_remove
    ]
    
    removed_count = original_count - len(cronjob_state["config"]["main_symbols"])
    
    if removed_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="None of the specified symbols were found in the configuration"
        )
    
    logger.info("Removed %d symbols by user: %s", removed_count, current_user.email)
    
    return {
        "message": f"Removed {removed_count} symbols",
        "removed_symbols": symbols_to_remove[:removed_count],
        "remaining_symbols": len(cronjob_state["config"]["main_symbols"])
    }

@router.put("/intervals")
async def update_intervals(
    intervals: Dict[str, int],
    current_user: User = Depends(get_current_user)
):
    """Update cronjob execution intervals."""
    
    # Validate intervals
    valid_keys = ["main_collection", "high_volume", "symbol_update", "status_report"]
    for key in intervals:
        if key not in valid_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interval key: {key}. Valid keys: {valid_keys}"
            )
        
        if intervals[key] < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Interval for {key} must be at least 10 seconds"
            )
    
    # Update intervals
    cronjob_state["config"]["intervals"].update(intervals)
    
    logger.info("Intervals updated by user: %s", current_user.email)
    
    return {
        "message": "Intervals updated successfully",
        "intervals": cronjob_state["config"]["intervals"]
    }

@router.post("/execute-now/{task_name}")
async def execute_task_now(
    task_name: str,
    current_user: User = Depends(get_current_user)
):
    """Execute a specific task immediately."""
    
    valid_tasks = ["main_collection", "high_volume", "symbol_update", "status_report"]
    
    if task_name not in valid_tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid task name: {task_name}. Valid tasks: {valid_tasks}"
        )
    
    # Execute the task
    try:
        if task_name == "main_collection":
            await execute_main_collection()
        elif task_name == "high_volume":
            await execute_high_volume_collection()
        elif task_name == "symbol_update":
            await execute_symbol_update()
        elif task_name == "status_report":
            await execute_status_report()
        
        logger.info("Task %s executed manually by user: %s", task_name, current_user.email)
        
        return {
            "message": f"Task {task_name} executed successfully",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error("Error executing task %s: %s", task_name, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute task: {str(e)}"
        )

@router.get("/logs")
async def get_cronjob_logs(
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get recent cronjob execution logs."""
    
    # This would typically come from a logging system
    # For now, return basic statistics
    return {
        "logs": [
            {
                "timestamp": cronjob_state["statistics"]["last_execution"],
                "status": "success" if cronjob_state["statistics"]["success_count"] > 0 else "unknown",
                "message": f"Total executions: {cronjob_state['statistics']['total_executions']}"
            }
        ],
        "statistics": cronjob_state["statistics"]
    }

# Background task functions
async def run_cronjob():
    """Main cronjob execution loop."""
    
    logger.info("Starting cronjob execution loop")
    
    try:
        while cronjob_state["is_running"]:
            current_time = time.time()
            config = cronjob_state["config"]
            intervals = config["intervals"]
            
            # Check if it's time to execute main collection
            if should_execute_task("main_collection", intervals["main_collection"]):
                cronjob_state["tasks"]["main_collection"] = asyncio.create_task(
                    execute_main_collection()
                )
            
            # Check if it's time to execute high volume collection
            if should_execute_task("high_volume", intervals["high_volume"]):
                cronjob_state["tasks"]["high_volume"] = asyncio.create_task(
                    execute_high_volume_collection()
                )
            
            # Check if it's time to update symbols
            if should_execute_task("symbol_update", intervals["symbol_update"]):
                cronjob_state["tasks"]["symbol_update"] = asyncio.create_task(
                    execute_symbol_update()
                )
            
            # Check if it's time to show status
            if should_execute_task("status_report", intervals["status_report"]):
                cronjob_state["tasks"]["status_report"] = asyncio.create_task(
                    execute_status_report()
                )
            
            # Clean up completed tasks
            cronjob_state["tasks"] = {
                name: task for name, task in cronjob_state["tasks"].items()
                if not task.done()
            }
            
            await asyncio.sleep(1)  # Check every second
            
    except asyncio.CancelledError:
        logger.info("Cronjob execution loop cancelled")
    except Exception as e:
        logger.error("Error in cronjob execution loop: %s", str(e))
        cronjob_state["is_running"] = False

def should_execute_task(task_name: str, interval: int) -> bool:
    """Check if a task should be executed based on its interval."""
    
    # Simple implementation - in production, you'd want to track last execution times
    return True  # For now, execute when called

async def execute_main_collection():
    """Execute main crypto data collection."""
    
    try:
        from app.services.data_feeder import data_feeder
        
        config = cronjob_state["config"]
        symbols = config["main_symbols"]
        timeframes = config["timeframes"]
        
        logger.info("Executing main collection for %d symbols", len(symbols))
        
        # Execute data collection
        await data_feeder.collect_market_data(symbols, timeframes)
        
        # Update statistics
        cronjob_state["statistics"]["total_executions"] += 1
        cronjob_state["statistics"]["success_count"] += 1
        cronjob_state["statistics"]["last_execution"] = datetime.now()
        
        logger.info("Main collection completed successfully")
        
    except Exception as e:
        logger.error("Error in main collection: %s", str(e))
        cronjob_state["statistics"]["error_count"] += 1

async def execute_high_volume_collection():
    """Execute high volume symbols collection."""
    
    try:
        from app.services.data_feeder import data_feeder
        from app.services.symbol_manager import symbol_manager
        
        logger.info("Executing high volume collection")
        
        # Get high volume symbols
        symbols = symbol_manager.get_top_volume_symbols(limit=30)
        
        if symbols:
            await data_feeder.collect_market_data(symbols, ["1m", "5m", "1h"])
        
        logger.info("High volume collection completed")
        
    except Exception as e:
        logger.error("Error in high volume collection: %s", str(e))

async def execute_symbol_update():
    """Execute symbol list update."""
    
    try:
        from app.services.symbol_manager import symbol_manager
        
        logger.info("Executing symbol update")
        
        symbol_manager.refresh_symbols()
        
        logger.info("Symbol update completed")
        
    except Exception as e:
        logger.error("Error in symbol update: %s", str(e))

async def execute_status_report():
    """Execute status report."""
    
    try:
        from app.core.database import SessionLocal
        from app.models.market_data import MarketData
        
        db = SessionLocal()
        
        # Get statistics
        total_records = db.query(MarketData).count()
        unique_symbols = db.query(MarketData.symbol).distinct().count()
        
        db.close()
        
        logger.info("Status report: %d records, %d symbols", total_records, unique_symbols)
        
    except Exception as e:
        logger.error("Error in status report: %s", str(e))

