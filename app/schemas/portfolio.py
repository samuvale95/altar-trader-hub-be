"""
Portfolio-related Pydantic schemas.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, validator


# Portfolio schemas
class PortfolioBase(BaseModel):
    """Base portfolio schema."""
    name: str
    description: Optional[str] = None


class PortfolioCreate(PortfolioBase):
    """Schema for portfolio creation."""
    pass


class PortfolioUpdate(BaseModel):
    """Schema for portfolio updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PortfolioResponse(PortfolioBase):
    """Schema for portfolio responses."""
    id: int
    user_id: int
    total_value: Decimal
    total_pnl: Decimal
    total_pnl_percentage: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Position schemas
class PositionBase(BaseModel):
    """Base position schema."""
    symbol: str
    quantity: Decimal
    avg_price: Decimal
    stop_loss_price: Optional[Decimal] = None
    take_profit_price: Optional[Decimal] = None
    max_loss: Optional[Decimal] = None


class PositionCreate(PositionBase):
    """Schema for position creation."""
    pass


class PositionUpdate(BaseModel):
    """Schema for position updates."""
    quantity: Optional[Decimal] = None
    avg_price: Optional[Decimal] = None
    stop_loss_price: Optional[Decimal] = None
    take_profit_price: Optional[Decimal] = None
    max_loss: Optional[Decimal] = None
    is_active: Optional[bool] = None


class PositionResponse(PositionBase):
    """Schema for position responses."""
    id: int
    portfolio_id: int
    base_asset: str
    quote_asset: str
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percentage: Decimal
    is_active: bool
    opened_at: datetime
    closed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Balance schemas
class BalanceResponse(BaseModel):
    """Schema for balance responses."""
    id: int
    portfolio_id: int
    exchange: str
    asset: str
    free: Decimal
    locked: Decimal
    total: Decimal
    usd_value: Decimal
    btc_value: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Portfolio summary schemas
class PortfolioSummary(BaseModel):
    """Schema for portfolio summary."""
    total_value: Decimal
    total_pnl: Decimal
    total_pnl_percentage: Decimal
    active_positions: int
    total_positions: int
    winning_positions: int
    losing_positions: int
    win_rate: Decimal
    best_performer: Optional[str] = None
    worst_performer: Optional[str] = None


class PositionSummary(BaseModel):
    """Schema for position summary."""
    symbol: str
    quantity: Decimal
    avg_price: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percentage: Decimal
    is_profitable: bool
