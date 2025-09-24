"""
Trading Strategies API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.trading_strategy import StrategyStatus, StrategyType, TradingStrategy, BacktestResult
from app.schemas.trading_strategy import (
    TradingStrategyCreate, TradingStrategyUpdate, TradingStrategyResponse,
    TradingStrategySummary, BacktestRequest, BacktestResultResponse,
    StrategyTradeResponse, StrategyExecutionResponse, StrategyPerformanceMetrics,
    StrategyListResponse, BacktestListResponse, StrategyControlRequest,
    AvailableStrategiesResponse, StrategyStatisticsResponse
)
from app.services.trading_strategy_service import TradingStrategyService
from app.services.symbol_manager import symbol_manager

router = APIRouter()


@router.get("/available", response_model=AvailableStrategiesResponse)
async def get_available_strategies():
    """Get list of available trading strategies."""
    strategies = [
        {
            "type": "dca",
            "name": "Dollar Cost Averaging",
            "description": "Invests a fixed amount at regular intervals",
            "risk_level": "Low",
            "parameters": {
                "investment_amount": {"type": "number", "default": 100, "min": 1, "max": 10000},
                "frequency": {"type": "integer", "default": 7, "min": 1, "max": 365},
                "max_investments": {"type": "integer", "default": 52, "min": 1, "max": 1000}
            }
        },
        {
            "type": "rsi",
            "name": "RSI Trading",
            "description": "Buys when RSI is oversold, sells when overbought",
            "risk_level": "Medium",
            "parameters": {
                "rsi_period": {"type": "integer", "default": 14, "min": 5, "max": 50},
                "oversold_threshold": {"type": "number", "default": 30, "min": 10, "max": 40},
                "overbought_threshold": {"type": "number", "default": 70, "min": 60, "max": 90}
            }
        },
        {
            "type": "macd",
            "name": "MACD Trading",
            "description": "Uses MACD line crossovers and histogram for signals",
            "risk_level": "Medium",
            "parameters": {
                "fast_period": {"type": "integer", "default": 12, "min": 5, "max": 50},
                "slow_period": {"type": "integer", "default": 26, "min": 10, "max": 100},
                "signal_period": {"type": "integer", "default": 9, "min": 5, "max": 50}
            }
        },
        {
            "type": "ma_crossover",
            "name": "Moving Average Crossover",
            "description": "Buys when fast MA crosses above slow MA",
            "risk_level": "Medium",
            "parameters": {
                "fast_period": {"type": "integer", "default": 10, "min": 5, "max": 50},
                "slow_period": {"type": "integer", "default": 30, "min": 10, "max": 200},
                "ma_type": {"type": "string", "default": "SMA", "options": ["SMA", "EMA"]}
            }
        },
        {
            "type": "bollinger_bands",
            "name": "Bollinger Bands",
            "description": "Trades based on price position relative to Bollinger Bands",
            "risk_level": "Medium",
            "parameters": {
                "period": {"type": "integer", "default": 20, "min": 5, "max": 100},
                "std_dev": {"type": "number", "default": 2.0, "min": 1.0, "max": 3.0}
            }
        },
        {
            "type": "range_trading",
            "name": "Range Trading",
            "description": "Buys at support levels, sells at resistance levels",
            "risk_level": "Medium",
            "parameters": {
                "lookback_period": {"type": "integer", "default": 20, "min": 5, "max": 100},
                "support_threshold": {"type": "number", "default": 0.02, "min": 0.01, "max": 0.1},
                "resistance_threshold": {"type": "number", "default": 0.02, "min": 0.01, "max": 0.1}
            }
        },
        {
            "type": "grid_trading",
            "name": "Grid Trading",
            "description": "Places buy/sell orders at regular price intervals",
            "risk_level": "High",
            "parameters": {
                "grid_size": {"type": "number", "default": 0.01, "min": 0.001, "max": 0.1},
                "grid_levels": {"type": "integer", "default": 10, "min": 5, "max": 50}
            }
        },
        {
            "type": "fear_greed",
            "name": "Fear & Greed Index",
            "description": "Trades based on market sentiment indicators",
            "risk_level": "High",
            "parameters": {
                "fear_threshold": {"type": "integer", "default": 25, "min": 10, "max": 40},
                "greed_threshold": {"type": "integer", "default": 75, "min": 60, "max": 90}
            }
        }
    ]
    
    return AvailableStrategiesResponse(strategies=strategies)


@router.post("/", response_model=TradingStrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: TradingStrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new trading strategy."""
    
    # Validate symbol before creating strategy
    if not symbol_manager.validate_symbol(strategy_data.symbol):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Symbol {strategy_data.symbol} is not valid or not tradable on Binance"
        )
    
    service = TradingStrategyService(db)
    return service.create_strategy(current_user.id, strategy_data)


@router.get("/", response_model=StrategyListResponse)
async def get_strategies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[StrategyStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's trading strategies."""
    service = TradingStrategyService(db)
    strategies = service.get_strategies(current_user.id, skip, limit, status)
    
    # Get total count
    total = db.query(TradingStrategy).filter(
        TradingStrategy.user_id == current_user.id
    ).count()
    
    return StrategyListResponse(
        strategies=strategies,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{strategy_id}", response_model=TradingStrategyResponse)
async def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific trading strategy."""
    service = TradingStrategyService(db)
    strategy = service.get_strategy(strategy_id, current_user.id)
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return strategy


@router.put("/{strategy_id}", response_model=TradingStrategyResponse)
async def update_strategy(
    strategy_id: int,
    update_data: TradingStrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a trading strategy."""
    service = TradingStrategyService(db)
    strategy = service.update_strategy(strategy_id, current_user.id, update_data)
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return strategy


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a trading strategy."""
    service = TradingStrategyService(db)
    success = service.delete_strategy(strategy_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found")


@router.post("/{strategy_id}/control", response_model=dict)
async def control_strategy(
    strategy_id: int,
    control_request: StrategyControlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Control strategy execution (start, stop, pause, resume)."""
    service = TradingStrategyService(db)
    
    action = control_request.action
    success = False
    
    if action == "start":
        success = service.start_strategy(strategy_id, current_user.id)
    elif action == "stop":
        success = service.stop_strategy(strategy_id, current_user.id)
    elif action == "pause":
        success = service.pause_strategy(strategy_id, current_user.id)
    elif action == "resume":
        success = service.resume_strategy(strategy_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to {action} strategy")
    
    return {"message": f"Strategy {action}ed successfully"}


@router.get("/{strategy_id}/performance", response_model=StrategyPerformanceMetrics)
async def get_strategy_performance(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get strategy performance metrics."""
    service = TradingStrategyService(db)
    
    try:
        return service.get_strategy_performance(strategy_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Strategy not found")


@router.get("/{strategy_id}/trades", response_model=List[StrategyTradeResponse])
async def get_strategy_trades(
    strategy_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get strategy trades."""
    service = TradingStrategyService(db)
    return service.get_strategy_trades(strategy_id, current_user.id, skip, limit)


@router.post("/{strategy_id}/backtest", response_model=BacktestResultResponse, status_code=status.HTTP_201_CREATED)
async def run_backtest(
    strategy_id: int,
    backtest_request: BacktestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run a backtest for a strategy."""
    service = TradingStrategyService(db)
    
    # Set strategy_id from URL
    backtest_request.strategy_id = strategy_id
    
    return service.run_backtest(current_user.id, backtest_request)


@router.get("/{strategy_id}/backtests", response_model=BacktestListResponse)
async def get_strategy_backtests(
    strategy_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get strategy backtest results."""
    service = TradingStrategyService(db)
    backtests = service.get_backtest_results(current_user.id, strategy_id, skip, limit)
    
    # Get total count
    total = db.query(BacktestResult).filter(
        BacktestResult.user_id == current_user.id,
        BacktestResult.strategy_id == strategy_id
    ).count()
    
    return BacktestListResponse(
        backtests=backtests,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/statistics/overview", response_model=StrategyStatisticsResponse)
async def get_strategy_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's strategy statistics overview."""
    service = TradingStrategyService(db)
    return service.get_strategy_statistics(current_user.id)


@router.get("/backtests/all", response_model=BacktestListResponse)
async def get_all_backtests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user's backtest results."""
    service = TradingStrategyService(db)
    backtests = service.get_backtest_results(current_user.id, None, skip, limit)
    
    # Get total count
    total = db.query(BacktestResult).filter(
        BacktestResult.user_id == current_user.id
    ).count()
    
    return BacktestListResponse(
        backtests=backtests,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )
