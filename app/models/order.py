"""
Order and trade-related database models.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class OrderSide(str, enum.Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT = "take_profit"
    TAKE_PROFIT_LIMIT = "take_profit_limit"


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Order(Base):
    """Order model for managing trading orders."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    
    # Order identification
    client_order_id = Column(String(100), unique=True, nullable=False)  # Our internal ID
    exchange_order_id = Column(String(100))  # Exchange's order ID
    
    # Order details
    symbol = Column(String(20), nullable=False)  # BTCUSDT, ETHUSDT, etc.
    side = Column(Enum(OrderSide), nullable=False)
    type = Column(Enum(OrderType), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8))  # For limit orders
    stop_price = Column(Numeric(20, 8))  # For stop orders
    
    # Execution details
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    filled_quantity = Column(Numeric(20, 8), default=0)
    remaining_quantity = Column(Numeric(20, 8), default=0)
    average_price = Column(Numeric(20, 8), default=0)
    
    # Fees and costs
    commission = Column(Numeric(20, 8), default=0)
    commission_asset = Column(String(10))  # USDT, BTC, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    filled_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    
    # Exchange and routing
    exchange = Column(String(50), nullable=False)  # binance, kraken, kucoin
    time_in_force = Column(String(10), default="GTC")  # GTC, IOC, FOK
    
    # Additional metadata
    metadata = Column(Text)  # JSON string for additional data
    
    # Relationships
    user = relationship("User", back_populates="orders")
    strategy = relationship("Strategy", back_populates="orders")
    trades = relationship("Trade", back_populates="order", cascade="all, delete-orphan")


class Trade(Base):
    """Trade model for tracking executed trades."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    exchange_trade_id = Column(String(100))  # Exchange's trade ID
    
    # Trade details
    symbol = Column(String(20), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    
    # Fees and costs
    commission = Column(Numeric(20, 8), default=0)
    commission_asset = Column(String(10))
    
    # P&L calculation
    cost_basis = Column(Numeric(20, 8), default=0)  # Total cost of the trade
    realized_pnl = Column(Numeric(20, 8), default=0)  # Realized P&L
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Exchange details
    exchange = Column(String(50), nullable=False)
    
    # Additional metadata
    metadata = Column(Text)  # JSON string for additional data
    
    # Relationships
    order = relationship("Order", back_populates="trades")
