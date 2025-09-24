"""
Strategy control API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.trading_strategy import TradingStrategy
from app.services.strategy_executor import strategy_executor
from app.core.logging import get_logger
from pydantic import BaseModel

router = APIRouter()
logger = get_logger(__name__)


class StrategyControlRequest(BaseModel):
    """Strategy control request model."""
    action: str  # "start", "stop", "restart"


@router.post("/{strategy_id}/start")
async def start_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a trading strategy."""
    
    # Check if strategy exists and belongs to user
    strategy = db.query(TradingStrategy).filter(
        TradingStrategy.id == strategy_id,
        TradingStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Start strategy
    success = await strategy_executor.start_strategy(strategy_id)
    
    if success:
        return {"message": f"Strategy {strategy.name} started successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start strategy"
        )


@router.post("/{strategy_id}/stop")
async def stop_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop a trading strategy."""
    
    # Check if strategy exists and belongs to user
    strategy = db.query(TradingStrategy).filter(
        TradingStrategy.id == strategy_id,
        TradingStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Stop strategy
    success = await strategy_executor.stop_strategy(strategy_id)
    
    if success:
        return {"message": f"Strategy {strategy.name} stopped successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop strategy"
        )


@router.post("/{strategy_id}/restart")
async def restart_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restart a trading strategy."""
    
    # Check if strategy exists and belongs to user
    strategy = db.query(TradingStrategy).filter(
        TradingStrategy.id == strategy_id,
        TradingStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Stop and start strategy
    await strategy_executor.stop_strategy(strategy_id)
    success = await strategy_executor.start_strategy(strategy_id)
    
    if success:
        return {"message": f"Strategy {strategy.name} restarted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart strategy"
        )


@router.post("/start-all")
async def start_all_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start all user's active strategies."""
    
    # Get user's strategies
    strategies = db.query(TradingStrategy).filter(
        TradingStrategy.user_id == current_user.id,
        TradingStrategy.is_active == True
    ).all()
    
    if not strategies:
        return {"message": "No active strategies found"}
    
    # Start all strategies
    started_count = 0
    for strategy in strategies:
        success = await strategy_executor.start_strategy(strategy.id)
        if success:
            started_count += 1
    
    return {
        "message": f"Started {started_count} out of {len(strategies)} strategies",
        "started_count": started_count,
        "total_count": len(strategies)
    }


@router.post("/stop-all")
async def stop_all_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop all user's strategies."""
    
    # Get user's strategies
    strategies = db.query(TradingStrategy).filter(
        TradingStrategy.user_id == current_user.id,
        TradingStrategy.is_active == True
    ).all()
    
    if not strategies:
        return {"message": "No active strategies found"}
    
    # Stop all strategies
    stopped_count = 0
    for strategy in strategies:
        success = await strategy_executor.stop_strategy(strategy.id)
        if success:
            stopped_count += 1
    
    return {
        "message": f"Stopped {stopped_count} out of {len(strategies)} strategies",
        "stopped_count": stopped_count,
        "total_count": len(strategies)
    }


@router.get("/status")
async def get_strategies_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of all user's strategies."""
    
    strategies = db.query(TradingStrategy).filter(
        TradingStrategy.user_id == current_user.id
    ).all()
    
    status_list = []
    for strategy in strategies:
        status_info = {
            "id": strategy.id,
            "name": strategy.name,
            "strategy_type": strategy.strategy_type.value,
            "status": strategy.status.value,
            "is_active": strategy.is_active,
            "started_at": strategy.started_at.isoformat() if strategy.started_at else None,
            "last_run_at": strategy.last_run_at.isoformat() if strategy.last_run_at else None,
            "total_trades": strategy.total_trades,
            "current_balance": str(strategy.current_balance)
        }
        status_list.append(status_info)
    
    return {
        "strategies": status_list,
        "total_strategies": len(strategies),
        "active_strategies": len([s for s in strategies if s.is_active])
    }

