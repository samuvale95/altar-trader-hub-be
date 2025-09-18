"""
Strategy API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.strategy import Strategy, StrategySignal, StrategyPerformance
from app.schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategySignalResponse,
    StrategyPerformanceResponse,
    StrategyExecution,
    StrategyBacktest,
    BacktestResult
)
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=List[StrategyResponse])
def get_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user strategies."""
    
    strategies = db.query(Strategy).filter(
        Strategy.user_id == current_user.id
    ).all()
    
    return strategies


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new strategy."""
    
    # Check if strategy name already exists for user
    existing_strategy = db.query(Strategy).filter(
        Strategy.user_id == current_user.id,
        Strategy.name == strategy_data.name
    ).first()
    
    if existing_strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strategy name already exists"
        )
    
    # Create strategy
    strategy = Strategy(
        user_id=current_user.id,
        name=strategy_data.name,
        description=strategy_data.description,
        strategy_type=strategy_data.strategy_type,
        config=strategy_data.config,
        symbols=strategy_data.symbols,
        timeframe=strategy_data.timeframe,
        max_position_size=strategy_data.max_position_size,
        stop_loss_percentage=strategy_data.stop_loss_percentage,
        take_profit_percentage=strategy_data.take_profit_percentage,
        max_daily_trades=strategy_data.max_daily_trades
    )
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    logger.info("Strategy created", strategy_id=strategy.id, user_id=current_user.id)
    
    return strategy


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific strategy."""
    
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    return strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a strategy."""
    
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Update strategy fields
    for field, value in strategy_data.dict(exclude_unset=True).items():
        setattr(strategy, field, value)
    
    db.commit()
    db.refresh(strategy)
    
    logger.info("Strategy updated", strategy_id=strategy.id, user_id=current_user.id)
    
    return strategy


@router.delete("/{strategy_id}")
def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a strategy."""
    
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Stop strategy if running
    if strategy.is_active:
        strategy.is_active = False
        strategy.stopped_at = db.func.now()
        db.commit()
    
    # Delete strategy
    db.delete(strategy)
    db.commit()
    
    logger.info("Strategy deleted", strategy_id=strategy_id, user_id=current_user.id)
    
    return {"message": "Strategy deleted successfully"}


@router.post("/{strategy_id}/start")
def start_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a strategy."""
    
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    if strategy.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strategy is already running"
        )
    
    # Start strategy
    strategy.is_active = True
    strategy.started_at = db.func.now()
    db.commit()
    
    logger.info("Strategy started", strategy_id=strategy.id, user_id=current_user.id)
    
    return {"message": "Strategy started successfully"}


@router.post("/{strategy_id}/stop")
def stop_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop a strategy."""
    
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    if not strategy.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strategy is not running"
        )
    
    # Stop strategy
    strategy.is_active = False
    strategy.stopped_at = db.func.now()
    db.commit()
    
    logger.info("Strategy stopped", strategy_id=strategy.id, user_id=current_user.id)
    
    return {"message": "Strategy stopped successfully"}


@router.get("/{strategy_id}/signals", response_model=List[StrategySignalResponse])
def get_strategy_signals(
    strategy_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get strategy signals."""
    
    # Verify strategy belongs to user
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Get signals
    signals = db.query(StrategySignal).filter(
        StrategySignal.strategy_id == strategy_id
    ).order_by(StrategySignal.timestamp.desc()).limit(limit).all()
    
    return signals


@router.get("/{strategy_id}/performance", response_model=List[StrategyPerformanceResponse])
def get_strategy_performance(
    strategy_id: int,
    period: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get strategy performance metrics."""
    
    # Verify strategy belongs to user
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Get performance data
    query = db.query(StrategyPerformance).filter(
        StrategyPerformance.strategy_id == strategy_id
    )
    
    if period:
        query = query.filter(StrategyPerformance.period == period)
    
    performance = query.order_by(StrategyPerformance.period_start.desc()).all()
    
    return performance


@router.post("/{strategy_id}/backtest")
def run_backtest(
    strategy_id: int,
    backtest_data: StrategyBacktest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run strategy backtest."""
    
    # Verify strategy belongs to user
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # TODO: Implement backtesting logic
    # This would involve:
    # 1. Fetching historical market data
    # 2. Running the strategy logic
    # 3. Calculating performance metrics
    # 4. Storing results
    
    logger.info("Backtest requested", strategy_id=strategy_id, user_id=current_user.id)
    
    return {"message": "Backtest started", "backtest_id": "bt_123456"}


@router.get("/{strategy_id}/backtest/{backtest_id}")
def get_backtest_result(
    strategy_id: int,
    backtest_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get backtest results."""
    
    # Verify strategy belongs to user
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # TODO: Implement backtest result retrieval
    # This would return the backtest results from the database
    
    return {"message": "Backtest results", "backtest_id": backtest_id}
