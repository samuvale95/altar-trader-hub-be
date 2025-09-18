"""
Trading Strategy Models for Paper Trading
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class StrategyStatus(enum.Enum):
    """Trading strategy status."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class StrategyType(enum.Enum):
    """Trading strategy types."""
    DCA = "dca"
    RSI = "rsi"
    MACD = "macd"
    MA_CROSSOVER = "ma_crossover"
    BOLLINGER_BANDS = "bollinger_bands"
    RANGE_TRADING = "range_trading"
    GRID_TRADING = "grid_trading"
    FEAR_GREED = "fear_greed"


class BacktestStatus(enum.Enum):
    """Backtest execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TradingStrategy(Base):
    """Trading strategy model."""
    
    __tablename__ = "trading_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Strategy configuration
    strategy_type = Column(Enum(StrategyType), nullable=False)
    parameters = Column(JSON, nullable=False)  # Strategy-specific parameters
    symbol = Column(String(20), nullable=False)  # Trading symbol (e.g., BTCUSDT)
    timeframe = Column(String(10), nullable=False)  # Timeframe (e.g., 1d, 1h)
    
    # Portfolio settings
    initial_balance = Column(Numeric(20, 8), nullable=False, default=10000.0)
    commission_rate = Column(Numeric(10, 6), nullable=False, default=0.001)
    
    # Status and control
    status = Column(Enum(StrategyStatus), default=StrategyStatus.INACTIVE)
    is_active = Column(Boolean, default=False)
    auto_start = Column(Boolean, default=False)
    
    # Performance tracking
    current_balance = Column(Numeric(20, 8), default=0)
    total_equity = Column(Numeric(20, 8), default=0)
    total_return = Column(Numeric(10, 6), default=0)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 4), default=0)
    max_drawdown = Column(Numeric(10, 6), default=0)
    sharpe_ratio = Column(Numeric(10, 6), default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_run_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    stopped_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="trading_strategies")
    backtests = relationship("BacktestResult", back_populates="strategy", cascade="all, delete-orphan")
    trades = relationship("StrategyTrade", back_populates="strategy", cascade="all, delete-orphan")


class BacktestResult(Base):
    """Backtest result model."""
    
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("trading_strategies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Backtest configuration
    name = Column(String(100), nullable=False)
    description = Column(Text)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    
    # Results
    status = Column(Enum(BacktestStatus), default=BacktestStatus.PENDING)
    total_periods = Column(Integer, default=0)
    
    # Performance metrics
    initial_balance = Column(Numeric(20, 8), nullable=False)
    final_balance = Column(Numeric(20, 8), default=0)
    total_equity = Column(Numeric(20, 8), default=0)
    total_return = Column(Numeric(10, 6), default=0)
    annualized_return = Column(Numeric(10, 6), default=0)
    volatility = Column(Numeric(10, 6), default=0)
    sharpe_ratio = Column(Numeric(10, 6), default=0)
    max_drawdown = Column(Numeric(10, 6), default=0)
    win_rate = Column(Numeric(5, 4), default=0)
    total_trades = Column(Integer, default=0)
    buy_trades = Column(Integer, default=0)
    sell_trades = Column(Integer, default=0)
    
    # Additional metrics
    buy_hold_return = Column(Numeric(10, 6), default=0)
    outperformance = Column(Numeric(10, 6), default=0)
    avg_trade_size = Column(Numeric(20, 8), default=0)
    trade_frequency = Column(Numeric(10, 6), default=0)
    
    # Error handling
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    strategy = relationship("TradingStrategy", back_populates="backtests")
    user = relationship("User")
    trades = relationship("BacktestTrade", back_populates="backtest", cascade="all, delete-orphan")


class StrategyTrade(Base):
    """Strategy trade model for live trading."""
    
    __tablename__ = "strategy_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("trading_strategies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Trade details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    commission = Column(Numeric(20, 8), default=0)
    
    # Signal information
    signal_strength = Column(Numeric(5, 4), default=0)
    reason = Column(Text)
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    strategy = relationship("TradingStrategy", back_populates="trades")
    user = relationship("User")


class BacktestTrade(Base):
    """Backtest trade model."""
    
    __tablename__ = "backtest_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtest_results.id"), nullable=False)
    
    # Trade details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    commission = Column(Numeric(20, 8), default=0)
    
    # Signal information
    signal_strength = Column(Numeric(5, 4), default=0)
    reason = Column(Text)
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    backtest = relationship("BacktestResult", back_populates="trades")


class StrategyExecution(Base):
    """Strategy execution log model."""
    
    __tablename__ = "strategy_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("trading_strategies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Execution details
    action = Column(String(50), nullable=False)  # START, STOP, PAUSE, RESUME, ERROR
    status = Column(String(20), nullable=False)  # SUCCESS, FAILED
    message = Column(Text)
    
    # Performance snapshot
    balance = Column(Numeric(20, 8), default=0)
    equity = Column(Numeric(20, 8), default=0)
    total_trades = Column(Integer, default=0)
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    strategy = relationship("TradingStrategy")
    user = relationship("User")
