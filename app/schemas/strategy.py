"""
Strategy-related Pydantic schemas.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, validator


# Strategy schemas
class StrategyBase(BaseModel):
    """Base strategy schema."""
    name: str
    description: Optional[str] = None
    strategy_type: str
    symbols: List[str]
    timeframe: str = "1h"
    max_position_size: Decimal = Decimal("10.0")
    stop_loss_percentage: Decimal = Decimal("2.0")
    take_profit_percentage: Decimal = Decimal("4.0")
    max_daily_trades: int = 10


class StrategyCreate(StrategyBase):
    """Schema for strategy creation."""
    config: Dict[str, Any] = {}
    
    @validator('strategy_type')
    def validate_strategy_type(cls, v):
        allowed_types = ['momentum', 'mean_reversion', 'arbitrage', 'scalping', 'swing', 'custom']
        if v.lower() not in allowed_types:
            raise ValueError(f'Strategy type must be one of: {allowed_types}')
        return v.lower()
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        allowed_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
        if v not in allowed_timeframes:
            raise ValueError(f'Timeframe must be one of: {allowed_timeframes}')
        return v


class StrategyUpdate(BaseModel):
    """Schema for strategy updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    symbols: Optional[List[str]] = None
    timeframe: Optional[str] = None
    max_position_size: Optional[Decimal] = None
    stop_loss_percentage: Optional[Decimal] = None
    take_profit_percentage: Optional[Decimal] = None
    max_daily_trades: Optional[int] = None
    is_active: Optional[bool] = None
    is_paper_trading: Optional[bool] = None


class StrategyResponse(StrategyBase):
    """Schema for strategy responses."""
    id: int
    user_id: int
    config: Dict[str, Any]
    is_active: bool
    is_paper_trading: bool
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: Decimal
    total_pnl_percentage: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_execution: Optional[datetime] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Strategy signal schemas
class StrategySignalResponse(BaseModel):
    """Schema for strategy signal responses."""
    id: int
    strategy_id: int
    symbol: str
    signal_type: str
    signal_strength: Decimal
    price: Decimal
    quantity: Optional[Decimal] = None
    timestamp: datetime
    indicators: Optional[Dict[str, Any]] = None
    confidence: Decimal
    reasoning: Optional[str] = None
    is_executed: bool
    executed_at: Optional[datetime] = None
    execution_price: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


# Strategy performance schemas
class StrategyPerformanceResponse(BaseModel):
    """Schema for strategy performance responses."""
    id: int
    strategy_id: int
    period: str
    period_start: datetime
    period_end: datetime
    total_return: Decimal
    annualized_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    calmar_ratio: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    gross_profit: Decimal
    gross_loss: Decimal
    net_profit: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


# Strategy execution schemas
class StrategyExecution(BaseModel):
    """Schema for strategy execution."""
    strategy_id: int
    action: str  # start, stop, pause, resume
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['start', 'stop', 'pause', 'resume']
        if v.lower() not in allowed_actions:
            raise ValueError(f'Action must be one of: {allowed_actions}')
        return v.lower()


class StrategyBacktest(BaseModel):
    """Schema for strategy backtesting."""
    strategy_id: int
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal = Decimal("10000.0")
    symbols: List[str]
    timeframe: str = "1h"


class BacktestResult(BaseModel):
    """Schema for backtest results."""
    strategy_id: int
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    final_capital: Decimal
    total_return: Decimal
    annualized_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    calmar_ratio: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    profit_factor: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    best_trade: Decimal
    worst_trade: Decimal
    created_at: datetime
