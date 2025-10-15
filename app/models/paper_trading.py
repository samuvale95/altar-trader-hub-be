"""
Paper Trading models for virtual portfolio management.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TradingMode(enum.Enum):
    """Trading mode enumeration."""
    PAPER = "paper"  # Virtual trading
    LIVE = "live"    # Real trading


class PaperPortfolio(Base):
    """Paper trading portfolio model."""
    
    __tablename__ = "paper_portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Trading mode
    mode = Column(
        SQLEnum(TradingMode, values_callable=lambda x: [e.value for e in x]),
        default=TradingMode.PAPER,
        nullable=False
    )
    
    # Initial capital
    initial_capital = Column(Numeric(20, 8), nullable=False, default=10000)  # Default $10,000
    
    # Current state
    cash_balance = Column(Numeric(20, 8), nullable=False)  # Available cash
    invested_value = Column(Numeric(20, 8), default=0)  # Value in positions
    total_value = Column(Numeric(20, 8), default=0)  # Total portfolio value
    
    # Performance metrics
    total_pnl = Column(Numeric(20, 8), default=0)  # Total profit/loss
    total_pnl_percentage = Column(Numeric(10, 4), default=0)  # Total P&L %
    realized_pnl = Column(Numeric(20, 8), default=0)  # Realized P&L (closed positions)
    unrealized_pnl = Column(Numeric(20, 8), default=0)  # Unrealized P&L (open positions)
    
    # Trading statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Numeric(10, 4), default=0)  # Win rate %
    
    # Risk metrics
    max_drawdown = Column(Numeric(10, 4), default=0)  # Maximum drawdown %
    sharpe_ratio = Column(Numeric(10, 4))  # Risk-adjusted return
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    positions = relationship("PaperPosition", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("PaperTrade", back_populates="portfolio", cascade="all, delete-orphan")
    balances = relationship("PaperBalance", back_populates="portfolio", cascade="all, delete-orphan")


class PaperPosition(Base):
    """Paper trading position model."""
    
    __tablename__ = "paper_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("paper_portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    
    # Position details
    quantity = Column(Numeric(20, 8), nullable=False)
    avg_entry_price = Column(Numeric(20, 8), nullable=False)
    current_price = Column(Numeric(20, 8), default=0)
    market_value = Column(Numeric(20, 8), default=0)
    
    # Cost basis
    total_cost = Column(Numeric(20, 8), nullable=False)  # Total invested
    
    # P&L
    unrealized_pnl = Column(Numeric(20, 8), default=0)
    unrealized_pnl_percentage = Column(Numeric(10, 4), default=0)
    
    # Risk management
    stop_loss_price = Column(Numeric(20, 8))
    take_profit_price = Column(Numeric(20, 8))
    
    # Status
    is_active = Column(Boolean, default=True)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("PaperPortfolio", back_populates="positions")


class PaperTrade(Base):
    """Paper trading trade history model."""
    
    __tablename__ = "paper_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("paper_portfolios.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("paper_positions.id"))
    
    # Trade details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    
    # Costs
    total_value = Column(Numeric(20, 8), nullable=False)  # quantity * price
    fee = Column(Numeric(20, 8), default=0)  # Trading fee
    total_cost = Column(Numeric(20, 8), nullable=False)  # total_value + fee
    
    # P&L (for sell orders)
    realized_pnl = Column(Numeric(20, 8), default=0)
    realized_pnl_percentage = Column(Numeric(10, 4), default=0)
    
    # Execution details
    order_type = Column(String(20), default="MARKET")  # MARKET, LIMIT, STOP_LOSS, etc.
    status = Column(String(20), default="FILLED")  # FILLED, PARTIAL, CANCELLED
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    portfolio = relationship("PaperPortfolio", back_populates="trades")


class PaperBalance(Base):
    """Paper trading balance model."""
    
    __tablename__ = "paper_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("paper_portfolios.id"), nullable=False)
    asset = Column(String(10), nullable=False)  # USDT, BTC, ETH, etc.
    
    # Balance details
    free = Column(Numeric(20, 8), default=0)  # Available
    locked = Column(Numeric(20, 8), default=0)  # Locked in orders
    total = Column(Numeric(20, 8), default=0)  # Total
    
    # Value
    usd_value = Column(Numeric(20, 8), default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("PaperPortfolio", back_populates="balances")

