"""
Order and trade-related Pydantic schemas.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, validator
from app.models.order import OrderSide, OrderType, OrderStatus


# Order schemas
class OrderBase(BaseModel):
    """Base order schema."""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: str = "GTC"


class OrderCreate(OrderBase):
    """Schema for order creation."""
    strategy_id: Optional[int] = None
    portfolio_id: Optional[int] = None
    exchange: str
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('exchange')
    def validate_exchange(cls, v):
        allowed_exchanges = ['binance', 'kraken', 'kucoin']
        if v.lower() not in allowed_exchanges:
            raise ValueError(f'Exchange must be one of: {allowed_exchanges}')
        return v.lower()
    
    @validator('time_in_force')
    def validate_time_in_force(cls, v):
        allowed_values = ['GTC', 'IOC', 'FOK']
        if v.upper() not in allowed_values:
            raise ValueError(f'Time in force must be one of: {allowed_values}')
        return v.upper()


class OrderUpdate(BaseModel):
    """Schema for order updates."""
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OrderResponse(OrderBase):
    """Schema for order responses."""
    id: int
    user_id: int
    strategy_id: Optional[int] = None
    portfolio_id: Optional[int] = None
    client_order_id: str
    exchange_order_id: Optional[str] = None
    status: OrderStatus
    filled_quantity: Decimal
    remaining_quantity: Decimal
    average_price: Decimal
    commission: Decimal
    commission_asset: Optional[str] = None
    exchange: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Trade schemas
class TradeResponse(BaseModel):
    """Schema for trade responses."""
    id: int
    order_id: int
    exchange_trade_id: Optional[str] = None
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal
    commission_asset: Optional[str] = None
    cost_basis: Decimal
    realized_pnl: Decimal
    exchange: str
    metadata: Optional[Dict[str, Any]] = None
    executed_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# Order management schemas
class OrderCancel(BaseModel):
    """Schema for order cancellation."""
    order_id: int
    reason: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    """Schema for order status updates."""
    order_id: int
    status: OrderStatus
    filled_quantity: Optional[Decimal] = None
    remaining_quantity: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    commission_asset: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Order summary schemas
class OrderSummary(BaseModel):
    """Schema for order summary."""
    total_orders: int
    pending_orders: int
    filled_orders: int
    cancelled_orders: int
    rejected_orders: int
    total_volume: Decimal
    total_commission: Decimal
    total_pnl: Decimal
    win_rate: Decimal


class TradeSummary(BaseModel):
    """Schema for trade summary."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_volume: Decimal
    total_commission: Decimal
    total_pnl: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: Decimal
    best_trade: Decimal
    worst_trade: Decimal


# Order filtering schemas
class OrderFilter(BaseModel):
    """Schema for order filtering."""
    symbol: Optional[str] = None
    side: Optional[OrderSide] = None
    type: Optional[OrderType] = None
    status: Optional[OrderStatus] = None
    exchange: Optional[str] = None
    strategy_id: Optional[int] = None
    portfolio_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class TradeFilter(BaseModel):
    """Schema for trade filtering."""
    symbol: Optional[str] = None
    side: Optional[OrderSide] = None
    exchange: Optional[str] = None
    order_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
