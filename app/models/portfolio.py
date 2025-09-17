"""
Portfolio-related database models.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Portfolio(Base):
    """Portfolio model for managing user portfolios."""
    
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    total_value = Column(Numeric(20, 8), default=0)  # Total portfolio value
    total_pnl = Column(Numeric(20, 8), default=0)   # Total P&L
    total_pnl_percentage = Column(Numeric(10, 4), default=0)  # Total P&L %
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    balances = relationship("Balance", back_populates="portfolio", cascade="all, delete-orphan")


class Position(Base):
    """Position model for tracking individual asset positions."""
    
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False)  # BTCUSDT, ETHUSDT, etc.
    base_asset = Column(String(10), nullable=False)  # BTC, ETH, etc.
    quote_asset = Column(String(10), nullable=False)  # USDT, BTC, etc.
    
    # Position details
    quantity = Column(Numeric(20, 8), nullable=False)  # Total quantity
    avg_price = Column(Numeric(20, 8), nullable=False)  # Average entry price
    current_price = Column(Numeric(20, 8), default=0)  # Current market price
    market_value = Column(Numeric(20, 8), default=0)  # Current market value
    unrealized_pnl = Column(Numeric(20, 8), default=0)  # Unrealized P&L
    unrealized_pnl_percentage = Column(Numeric(10, 4), default=0)  # Unrealized P&L %
    
    # Risk management
    stop_loss_price = Column(Numeric(20, 8))
    take_profit_price = Column(Numeric(20, 8))
    max_loss = Column(Numeric(20, 8))  # Maximum loss allowed
    
    # Status
    is_active = Column(Boolean, default=True)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")


class Balance(Base):
    """Balance model for tracking exchange balances."""
    
    __tablename__ = "balances"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    exchange = Column(String(50), nullable=False)  # binance, kraken, kucoin
    asset = Column(String(10), nullable=False)  # BTC, ETH, USDT, etc.
    
    # Balance details
    free = Column(Numeric(20, 8), default=0)  # Available balance
    locked = Column(Numeric(20, 8), default=0)  # Locked in orders
    total = Column(Numeric(20, 8), default=0)  # Total balance
    
    # Value in base currency
    usd_value = Column(Numeric(20, 8), default=0)  # Value in USD
    btc_value = Column(Numeric(20, 8), default=0)  # Value in BTC
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True))
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="balances")
