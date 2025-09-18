"""
Pydantic schemas for Trading Strategy models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from app.models.trading_strategy import StrategyStatus, StrategyType, BacktestStatus


class TradingStrategyBase(BaseModel):
    """Base schema for trading strategy."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    strategy_type: StrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    symbol: str = Field(..., min_length=1, max_length=20)
    timeframe: str = Field(..., min_length=1, max_length=10)
    initial_balance: Decimal = Field(..., gt=0)
    commission_rate: Decimal = Field(..., ge=0, le=1)
    auto_start: bool = False


class TradingStrategyCreate(TradingStrategyBase):
    """Schema for creating a trading strategy."""
    pass


class TradingStrategyUpdate(BaseModel):
    """Schema for updating a trading strategy."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    symbol: Optional[str] = Field(None, min_length=1, max_length=20)
    timeframe: Optional[str] = Field(None, min_length=1, max_length=10)
    initial_balance: Optional[Decimal] = Field(None, gt=0)
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    auto_start: Optional[bool] = None


class TradingStrategyResponse(TradingStrategyBase):
    """Schema for trading strategy response."""
    id: int
    user_id: int
    status: StrategyStatus
    is_active: bool
    current_balance: Decimal
    total_equity: Decimal
    total_return: Decimal
    total_trades: int
    win_rate: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    created_at: datetime
    updated_at: Optional[datetime]
    last_run_at: Optional[datetime]
    started_at: Optional[datetime]
    stopped_at: Optional[datetime]

    class Config:
        from_attributes = True


class TradingStrategySummary(BaseModel):
    """Schema for trading strategy summary."""
    id: int
    name: str
    strategy_type: StrategyType
    symbol: str
    timeframe: str
    status: StrategyStatus
    is_active: bool
    total_return: Decimal
    total_trades: int
    win_rate: Decimal
    created_at: datetime
    last_run_at: Optional[datetime]

    class Config:
        from_attributes = True


class BacktestResultBase(BaseModel):
    """Base schema for backtest result."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    symbol: str = Field(..., min_length=1, max_length=20)
    timeframe: str = Field(..., min_length=1, max_length=10)


class BacktestResultCreate(BacktestResultBase):
    """Schema for creating a backtest result."""
    strategy_id: int


class BacktestResultResponse(BacktestResultBase):
    """Schema for backtest result response."""
    id: int
    strategy_id: int
    user_id: int
    status: BacktestStatus
    total_periods: int
    initial_balance: Decimal
    final_balance: Decimal
    total_equity: Decimal
    total_return: Decimal
    annualized_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    total_trades: int
    buy_trades: int
    sell_trades: int
    buy_hold_return: Decimal
    outperformance: Decimal
    avg_trade_size: Decimal
    trade_frequency: Decimal
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class StrategyTradeResponse(BaseModel):
    """Schema for strategy trade response."""
    id: int
    strategy_id: int
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    commission: Decimal
    signal_strength: Decimal
    reason: Optional[str]
    executed_at: datetime

    class Config:
        from_attributes = True


class BacktestTradeResponse(BaseModel):
    """Schema for backtest trade response."""
    id: int
    backtest_id: int
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    commission: Decimal
    signal_strength: Decimal
    reason: Optional[str]
    executed_at: datetime

    class Config:
        from_attributes = True


class StrategyExecutionResponse(BaseModel):
    """Schema for strategy execution response."""
    id: int
    strategy_id: int
    action: str
    status: str
    message: Optional[str]
    balance: Decimal
    equity: Decimal
    total_trades: int
    executed_at: datetime

    class Config:
        from_attributes = True


class StrategyPerformanceMetrics(BaseModel):
    """Schema for strategy performance metrics."""
    total_return: Decimal
    annualized_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    total_trades: int
    buy_trades: int
    sell_trades: int
    avg_trade_size: Decimal
    trade_frequency: Decimal
    current_balance: Decimal
    total_equity: Decimal


class StrategyListResponse(BaseModel):
    """Schema for strategy list response."""
    strategies: List[TradingStrategySummary]
    total: int
    page: int
    size: int
    pages: int


class BacktestListResponse(BaseModel):
    """Schema for backtest list response."""
    backtests: List[BacktestResultResponse]
    total: int
    page: int
    size: int
    pages: int


class StrategyControlRequest(BaseModel):
    """Schema for strategy control requests."""
    action: str = Field(..., pattern="^(start|stop|pause|resume)$")
    message: Optional[str] = None


class BacktestRequest(BaseModel):
    """Schema for backtest execution request."""
    strategy_id: int
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    symbol: Optional[str] = None
    timeframe: Optional[str] = None


class StrategyParametersSchema(BaseModel):
    """Schema for strategy parameters validation."""
    strategy_type: StrategyType
    parameters: Dict[str, Any]

    @validator('parameters')
    def validate_parameters(cls, v, values):
        """Validate strategy-specific parameters."""
        strategy_type = values.get('strategy_type')
        
        if strategy_type == StrategyType.DCA:
            required_params = ['investment_amount', 'frequency', 'max_investments']
        elif strategy_type == StrategyType.RSI:
            required_params = ['rsi_period', 'oversold_threshold', 'overbought_threshold']
        elif strategy_type == StrategyType.MACD:
            required_params = ['fast_period', 'slow_period', 'signal_period']
        elif strategy_type == StrategyType.MA_CROSSOVER:
            required_params = ['fast_period', 'slow_period', 'ma_type']
        elif strategy_type == StrategyType.BOLLINGER_BANDS:
            required_params = ['period', 'std_dev']
        elif strategy_type == StrategyType.RANGE_TRADING:
            required_params = ['lookback_period', 'support_threshold', 'resistance_threshold']
        elif strategy_type == StrategyType.GRID_TRADING:
            required_params = ['grid_size', 'grid_levels']
        elif strategy_type == StrategyType.FEAR_GREED:
            required_params = ['fear_threshold', 'greed_threshold']
        else:
            return v
        
        missing_params = [param for param in required_params if param not in v]
        if missing_params:
            raise ValueError(f"Missing required parameters for {strategy_type.value}: {missing_params}")
        
        return v


class AvailableStrategiesResponse(BaseModel):
    """Schema for available strategies response."""
    strategies: List[Dict[str, Any]]


class StrategyStatisticsResponse(BaseModel):
    """Schema for strategy statistics response."""
    total_strategies: int
    active_strategies: int
    total_backtests: int
    running_backtests: int
    total_trades: int
    total_profit: Decimal
    best_strategy: Optional[str]
    worst_strategy: Optional[str]
