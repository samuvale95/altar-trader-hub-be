"""
Strategy-related database models.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Strategy(Base):
    """Strategy model for trading strategies."""
    
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False)  # momentum, mean_reversion, arbitrage, etc.
    
    # Strategy configuration
    config = Column(JSON)  # Strategy-specific parameters
    symbols = Column(JSON)  # List of trading symbols
    timeframe = Column(String(10), default="1h")  # 1m, 5m, 15m, 1h, 4h, 1d
    
    # Risk management
    max_position_size = Column(Numeric(10, 4), default=10.0)  # Max position size as %
    stop_loss_percentage = Column(Numeric(10, 4), default=2.0)  # Stop loss %
    take_profit_percentage = Column(Numeric(10, 4), default=4.0)  # Take profit %
    max_daily_trades = Column(Integer, default=10)
    
    # Status and performance
    is_active = Column(Boolean, default=False)
    is_paper_trading = Column(Boolean, default=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Numeric(20, 8), default=0)
    total_pnl_percentage = Column(Numeric(10, 4), default=0)
    max_drawdown = Column(Numeric(10, 4), default=0)
    sharpe_ratio = Column(Numeric(10, 4), default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_execution = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    stopped_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="strategies")
    signals = relationship("StrategySignal", back_populates="strategy", cascade="all, delete-orphan")
    performance = relationship("StrategyPerformance", back_populates="strategy", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="strategy")


class StrategySignal(Base):
    """Strategy signal model for tracking trading signals."""
    
    __tablename__ = "strategy_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    signal_type = Column(String(20), nullable=False)  # buy, sell, hold
    signal_strength = Column(Numeric(5, 4), default=0)  # Signal strength 0-1
    
    # Price and timing
    price = Column(Numeric(20, 8), nullable=False)
    quantity = Column(Numeric(20, 8))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Technical indicators
    indicators = Column(JSON)  # RSI, MACD, Bollinger Bands, etc.
    
    # Signal metadata
    confidence = Column(Numeric(5, 4), default=0)  # Confidence level 0-1
    reasoning = Column(Text)  # Human-readable explanation
    
    # Status
    is_executed = Column(Boolean, default=False)
    executed_at = Column(DateTime(timezone=True))
    execution_price = Column(Numeric(20, 8))
    
    # Relationships
    strategy = relationship("Strategy", back_populates="signals")


class StrategyPerformance(Base):
    """Strategy performance metrics over time."""
    
    __tablename__ = "strategy_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    period = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    
    # Performance metrics
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Returns
    total_return = Column(Numeric(10, 4), default=0)  # Total return %
    annualized_return = Column(Numeric(10, 4), default=0)  # Annualized return %
    
    # Risk metrics
    volatility = Column(Numeric(10, 4), default=0)  # Volatility %
    sharpe_ratio = Column(Numeric(10, 4), default=0)  # Sharpe ratio
    max_drawdown = Column(Numeric(10, 4), default=0)  # Maximum drawdown %
    calmar_ratio = Column(Numeric(10, 4), default=0)  # Calmar ratio
    
    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 4), default=0)  # Win rate %
    
    # P&L
    gross_profit = Column(Numeric(20, 8), default=0)
    gross_loss = Column(Numeric(20, 8), default=0)
    net_profit = Column(Numeric(20, 8), default=0)
    
    # Average metrics
    avg_win = Column(Numeric(20, 8), default=0)
    avg_loss = Column(Numeric(20, 8), default=0)
    profit_factor = Column(Numeric(10, 4), default=0)  # Gross profit / Gross loss
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    strategy = relationship("Strategy", back_populates="performance")
