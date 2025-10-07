"""
Data collector API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user
from app.models.user import User
from app.services.data_feeder import data_feeder
from app.services.task_manager import task_manager, TaskStatus
from app.core.logging import get_logger
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
logger = get_logger(__name__)


class SchedulerConfigRequest(BaseModel):
    """Scheduler configuration request model."""
    collection_interval: Optional[int] = None  # seconds
    symbol_refresh_interval: Optional[int] = None  # seconds
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    enabled: Optional[bool] = None


class DataCollectionStatus(BaseModel):
    """Data collection status model."""
    is_running: bool
    symbols_count: int
    active_tasks: int
    collection_interval: int
    symbols: List[str]


class TaskResponse(BaseModel):
    """Task response model."""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Task status response model."""
    task_id: str
    task_type: str
    status: str
    progress: int
    message: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[dict] = None


@router.post("/start")
async def start_scheduler(
    current_user: User = Depends(get_current_user)
):
    """Start the data collection scheduler."""
    
    try:
        from app.services.data_scheduler import data_scheduler
        
        if data_scheduler.is_running:
            return {"message": "Data collection scheduler is already running"}
        
        await data_scheduler.start_scheduler()
        logger.info("Data collection scheduler started manually", user_id=current_user.id)
        
        return {"message": "Data collection scheduler started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start data collection scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start data collection scheduler: {str(e)}"
        )


@router.post("/stop")
async def stop_scheduler(
    current_user: User = Depends(get_current_user)
):
    """Stop the data collection scheduler."""
    
    try:
        from app.services.data_scheduler import data_scheduler
        
        if not data_scheduler.is_running:
            return {"message": "Data collection scheduler is not running"}
        
        await data_scheduler.stop_scheduler()
        logger.info("Data collection scheduler stopped manually", user_id=current_user.id)
        
        return {"message": "Data collection scheduler stopped successfully"}
        
    except Exception as e:
        logger.error(f"Failed to stop data collection scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop data collection scheduler: {str(e)}"
        )


@router.get("/status")
async def get_collection_status(
    current_user: User = Depends(get_current_user)
):
    """Get data collection scheduler status."""
    
    try:
        from app.services.data_scheduler import data_scheduler
        
        # Get scheduler status
        scheduler_status = data_scheduler.get_scheduler_status()
        
        # Get active tasks count
        active_tasks = task_manager.get_active_tasks()
        
        # Get current symbols from data feeder
        current_symbols = data_feeder.symbols
        
        status = {
            "scheduler": {
                "is_running": scheduler_status["is_running"],
                "collection_interval": scheduler_status["collection_interval"],
                "symbol_refresh_interval": scheduler_status["symbol_refresh_interval"],
                "data_collection_running": scheduler_status["data_collection_running"],
                "active_tasks_count": scheduler_status["active_tasks_count"],
                "scheduler_task_types": scheduler_status["scheduler_task_types"]
            },
            "data_feeder": {
                "symbols_count": len(current_symbols),
                "symbols": current_symbols[:10],  # Show first 10 symbols
                "timeframes": data_feeder.timeframes
            },
            "task_manager": {
                "active_tasks": len(active_tasks),
                "task_counts": task_manager.get_task_count()
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get collection status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection status: {str(e)}"
        )


@router.get("/latest-prices")
async def get_latest_prices(
    symbols: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get latest prices for symbols."""
    
    try:
        db = SessionLocal()
        try:
            from app.models.market_data import MarketData
            latest_prices = []
            
            if symbols:
                # Get specific symbols
                symbol_list = [s.strip().upper() for s in symbols.split(",")]
                for symbol in symbol_list:
                    latest = db.query(MarketData).filter(
                        MarketData.symbol == symbol
                    ).order_by(MarketData.timestamp.desc()).first()
                    if latest:
                        latest_prices.append({
                            "symbol": symbol,
                            "price": float(latest.close_price),
                            "timestamp": latest.timestamp.isoformat(),
                            "timeframe": latest.timeframe
                        })
            else:
                # Get latest prices for all available symbols (limited)
                distinct_symbols = db.query(MarketData.symbol).distinct().limit(limit).all()
                for (symbol,) in distinct_symbols:
                    latest = db.query(MarketData).filter(
                        MarketData.symbol == symbol
                    ).order_by(MarketData.timestamp.desc()).first()
                    if latest:
                        latest_prices.append({
                            "symbol": symbol,
                            "price": float(latest.close_price),
                            "timestamp": latest.timestamp.isoformat(),
                            "timeframe": latest.timeframe
                        })
            
            return {
                "latest_prices": latest_prices,
                "count": len(latest_prices),
                "requested_symbols": symbol_list if symbols else "all",
                "limit": limit
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to get latest prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest prices: {str(e)}"
        )


@router.post("/refresh-symbols", response_model=TaskResponse)
async def refresh_symbols(
    current_user: User = Depends(get_current_user)
):
    """Refresh symbol list asynchronously."""
    
    try:
        # Submit refresh task to background
        task_id = await task_manager.submit_task(
            "symbol_refresh",
            data_feeder.refresh_symbols_async
        )
        
        logger.info("Symbol refresh task submitted", task_id=task_id, user_id=current_user.id)
        
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message="Symbol refresh task submitted successfully. Use the task_id to check status."
        )
        
    except Exception as e:
        logger.error(f"Failed to submit symbol refresh task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit symbol refresh task: {str(e)}"
        )


@router.get("/config")
async def get_scheduler_config(
    current_user: User = Depends(get_current_user)
):
    """Get current scheduler configuration."""
    
    try:
        from app.services.data_scheduler import data_scheduler
        
        config = {
            "collection_interval": data_scheduler.collection_interval,
            "symbol_refresh_interval": data_scheduler.symbol_refresh_interval,
            "is_running": data_scheduler.is_running,
            "symbols": data_feeder.symbols,
            "timeframes": data_feeder.timeframes,
            "available_symbols": data_feeder.get_available_symbols(limit=50)
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get scheduler config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduler config: {str(e)}"
        )


@router.put("/config")
async def update_scheduler_config(
    request: SchedulerConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Update scheduler configuration."""
    
    try:
        from app.services.data_scheduler import data_scheduler
        
        # Update collection interval
        if request.collection_interval is not None:
            if request.collection_interval < 60:  # Minimum 1 minute
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Collection interval must be at least 60 seconds"
                )
            data_scheduler.collection_interval = request.collection_interval
            logger.info(f"Collection interval updated to {request.collection_interval}s", user_id=current_user.id)
        
        # Update symbol refresh interval
        if request.symbol_refresh_interval is not None:
            if request.symbol_refresh_interval < 300:  # Minimum 5 minutes
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Symbol refresh interval must be at least 300 seconds"
                )
            data_scheduler.symbol_refresh_interval = request.symbol_refresh_interval
            logger.info(f"Symbol refresh interval updated to {request.symbol_refresh_interval}s", user_id=current_user.id)
        
        # Update symbols
        if request.symbols is not None:
            if len(request.symbols) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one symbol must be specified"
                )
            data_feeder.symbols = request.symbols
            logger.info(f"Symbols updated to {len(request.symbols)} symbols", user_id=current_user.id)
        
        # Update timeframes
        if request.timeframes is not None:
            allowed_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
            invalid_timeframes = [tf for tf in request.timeframes if tf not in allowed_timeframes]
            if invalid_timeframes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid timeframes: {invalid_timeframes}. Allowed: {allowed_timeframes}"
                )
            data_feeder.timeframes = request.timeframes
            logger.info(f"Timeframes updated to {request.timeframes}", user_id=current_user.id)
        
        # Enable/disable scheduler
        if request.enabled is not None:
            if request.enabled and not data_scheduler.is_running:
                await data_scheduler.start_scheduler()
                logger.info("Scheduler enabled", user_id=current_user.id)
            elif not request.enabled and data_scheduler.is_running:
                await data_scheduler.stop_scheduler()
                logger.info("Scheduler disabled", user_id=current_user.id)
        
        return {
            "message": "Scheduler configuration updated successfully",
            "config": {
                "collection_interval": data_scheduler.collection_interval,
                "symbol_refresh_interval": data_scheduler.symbol_refresh_interval,
                "is_running": data_scheduler.is_running,
                "symbols": data_feeder.symbols,
                "timeframes": data_feeder.timeframes
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update scheduler config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scheduler config: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a specific task."""
    
    try:
        task_info = task_manager.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskStatusResponse(
            task_id=task_info.task_id,
            task_type=task_info.task_type,
            status=task_info.status.value,
            progress=task_info.progress,
            message=task_info.message,
            created_at=task_info.created_at.isoformat(),
            started_at=task_info.started_at.isoformat() if task_info.started_at else None,
            completed_at=task_info.completed_at.isoformat() if task_info.completed_at else None,
            error=task_info.error,
            result=task_info.result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/tasks", response_model=List[TaskStatusResponse])
async def get_all_tasks(
    task_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all tasks or tasks by type."""
    
    try:
        if task_type:
            tasks = task_manager.get_tasks_by_type(task_type)
        else:
            tasks = task_manager.get_all_tasks()
        
        response = []
        for task_info in tasks.values():
            response.append(TaskStatusResponse(
                task_id=task_info.task_id,
                task_type=task_info.task_type,
                status=task_info.status.value,
                progress=task_info.progress,
                message=task_info.message,
                created_at=task_info.created_at.isoformat(),
                started_at=task_info.started_at.isoformat() if task_info.started_at else None,
                completed_at=task_info.completed_at.isoformat() if task_info.completed_at else None,
                error=task_info.error,
                result=task_info.result
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks: {str(e)}"
        )


@router.get("/tasks/active", response_model=List[TaskStatusResponse])
async def get_active_tasks(
    current_user: User = Depends(get_current_user)
):
    """Get all active tasks."""
    
    try:
        tasks = task_manager.get_active_tasks()
        
        response = []
        for task_info in tasks.values():
            response.append(TaskStatusResponse(
                task_id=task_info.task_id,
                task_type=task_info.task_type,
                status=task_info.status.value,
                progress=task_info.progress,
                message=task_info.message,
                created_at=task_info.created_at.isoformat(),
                started_at=task_info.started_at.isoformat() if task_info.started_at else None,
                completed_at=task_info.completed_at.isoformat() if task_info.completed_at else None,
                error=task_info.error,
                result=task_info.result
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get active tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active tasks: {str(e)}"
        )


@router.post("/task/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a running task."""
    
    try:
        success = await task_manager.cancel_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or cannot be cancelled"
            )
        
        return {"message": f"Task {task_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.get("/tasks/stats")
async def get_task_stats(
    current_user: User = Depends(get_current_user)
):
    """Get task statistics."""
    
    try:
        stats = task_manager.get_task_count()
        active_tasks = task_manager.get_active_tasks()
        
        return {
            "task_counts": stats,
            "active_tasks_count": len(active_tasks),
            "data_collector_status": {
                "symbols_count": len(data_feeder.symbols),
                "timeframes": data_feeder.timeframes,
                "available_symbols": data_feeder.get_available_symbols(limit=10)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task stats: {str(e)}"
        )

