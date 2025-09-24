"""
System monitoring API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.trading_strategy import TradingStrategy
from app.core.logging import get_logger
from datetime import datetime, timedelta
import psutil
import os
import time
from pydantic import BaseModel

router = APIRouter()
logger = get_logger(__name__)


class SystemStatus(BaseModel):
    """System status response model."""
    status: str
    uptime_seconds: int
    uptime_human: str
    start_time: str
    version: str
    environment: str
    memory_usage_mb: float
    cpu_usage_percent: float
    active_strategies: int
    total_strategies: int


class StrategyUptime(BaseModel):
    """Strategy uptime response model."""
    strategy_id: int
    strategy_name: str
    status: str
    is_active: bool
    started_at: str
    uptime_seconds: int
    uptime_human: str
    last_run_at: str
    total_trades: int
    current_balance: str


@router.get("/status", response_model=SystemStatus)
def get_system_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system status and uptime information."""
    
    try:
        # Get process uptime
        process = psutil.Process(os.getpid())
        start_time = datetime.fromtimestamp(process.create_time())
        uptime_seconds = int(time.time() - process.create_time())
        uptime_human = _format_uptime(uptime_seconds)
        
        # Get memory and CPU usage
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        cpu_usage_percent = process.cpu_percent()
        
        # Get strategy counts
        total_strategies = db.query(TradingStrategy).count()
        active_strategies = db.query(TradingStrategy).filter(TradingStrategy.is_active == True).count()
        
        return SystemStatus(
            status="healthy",
            uptime_seconds=uptime_seconds,
            uptime_human=uptime_human,
            start_time=start_time.isoformat(),
            version="0.1.0",
            environment="development",
            memory_usage_mb=round(memory_usage_mb, 2),
            cpu_usage_percent=round(cpu_usage_percent, 2),
            active_strategies=active_strategies,
            total_strategies=total_strategies
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system status: {str(e)}"
        )


@router.get("/strategies/uptime", response_model=list[StrategyUptime])
def get_strategies_uptime(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get uptime information for all strategies."""
    
    try:
        strategies = db.query(TradingStrategy).filter(
            TradingStrategy.user_id == current_user.id
        ).all()
        
        strategy_uptimes = []
        for strategy in strategies:
            uptime_seconds = 0
            uptime_human = "Not started"
            
            if strategy.started_at:
                uptime_seconds = int((datetime.utcnow() - strategy.started_at).total_seconds())
                uptime_human = _format_uptime(uptime_seconds)
            
            strategy_uptime = StrategyUptime(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                status=strategy.status.value,
                is_active=strategy.is_active,
                started_at=strategy.started_at.isoformat() if strategy.started_at else "Never",
                uptime_seconds=uptime_seconds,
                uptime_human=uptime_human,
                last_run_at=strategy.last_run_at.isoformat() if strategy.last_run_at else "Never",
                total_trades=strategy.total_trades,
                current_balance=str(strategy.current_balance)
            )
            
            strategy_uptimes.append(strategy_uptime)
        
        return strategy_uptimes
        
    except Exception as e:
        logger.error(f"Failed to get strategies uptime: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve strategies uptime: {str(e)}"
        )


@router.get("/uptime")
def get_uptime(
    current_user: User = Depends(get_current_user)
):
    """Get simple uptime information."""
    
    try:
        process = psutil.Process(os.getpid())
        start_time = datetime.fromtimestamp(process.create_time())
        uptime_seconds = int(time.time() - process.create_time())
        uptime_human = _format_uptime(uptime_seconds)
        
        return {
            "uptime_seconds": uptime_seconds,
            "uptime_human": uptime_human,
            "start_time": start_time.isoformat(),
            "current_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get uptime: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve uptime: {str(e)}"
        )


def _format_uptime(seconds: int) -> str:
    """Format uptime in human readable format."""
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    elif seconds < 86400:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m"
    else:
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        return f"{days}d {remaining_hours}h"

