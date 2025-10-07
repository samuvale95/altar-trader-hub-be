"""
Paper Trading Pydantic schemas.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, validator


# Portfolio schemas

class PaperPortfolioCreate(BaseModel):
    """Schema for creating a paper portfolio."""
    name: str
    description: Optional[str] = None
    initial_capital: Decimal = Decimal("10000.00")
    
    @validator('initial_capital')
    def validate_initial_capital(cls, v):
        if v <= 0:
            raise ValueError('Initial capital must be positive')
        if v > 1000000:
            raise ValueError('Initial capital cannot exceed $1,000,000')
        return v


class PaperPortfolioResponse(BaseModel):
    """Schema for paper portfolio responses."""
    id: int
    name: str
    description: Optional[str]
    mode: str
    initial_capital: float
    cash_balance: float
    invested_value: float
    total_value: float
    total_pnl: float
    total_pnl_percentage: float
    realized_pnl: float
    unrealized_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    created_at: str
    updated_at: Optional[str]


# Position schemas

class PaperPositionResponse(BaseModel):
    """Schema for paper position responses."""
    id: int
    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float
    market_value: float
    total_cost: float
    unrealized_pnl: float
    unrealized_pnl_percentage: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    opened_at: str


# Trade schemas

class TradeRequest(BaseModel):
    """Schema for trade requests."""
    symbol: str
    quantity: Decimal
    price: Optional[Decimal] = None  # Market price if None
    order_type: str = "MARKET"
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or len(v) < 6:
            raise ValueError('Invalid symbol format')
        return v.upper()
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @validator('order_type')
    def validate_order_type(cls, v):
        allowed_types = ['MARKET', 'LIMIT']
        if v.upper() not in allowed_types:
            raise ValueError(f'Order type must be one of: {allowed_types}')
        return v.upper()


class TradeResponse(BaseModel):
    """Schema for trade responses."""
    trade_id: int
    symbol: str
    side: str
    quantity: float
    price: float
    total_cost: float
    fee: float
    realized_pnl: Optional[float] = None
    realized_pnl_percentage: Optional[float] = None
    status: str
    executed_at: str


class TradeHistoryResponse(BaseModel):
    """Schema for trade history."""
    id: int
    symbol: str
    side: str
    quantity: float
    price: float
    total_value: float
    fee: float
    total_cost: float
    realized_pnl: float
    realized_pnl_percentage: float
    order_type: str
    status: str
    executed_at: str


# Risk management schemas

class SetStopLossRequest(BaseModel):
    """Schema for setting stop loss."""
    stop_loss_price: Decimal
    
    @validator('stop_loss_price')
    def validate_stop_loss(cls, v):
        if v <= 0:
            raise ValueError('Stop loss price must be positive')
        return v


class SetTakeProfitRequest(BaseModel):
    """Schema for setting take profit."""
    take_profit_price: Decimal
    
    @validator('take_profit_price')
    def validate_take_profit(cls, v):
        if v <= 0:
            raise ValueError('Take profit price must be positive')
        return v


# Balance schemas

class BalanceResponse(BaseModel):
    """Schema for balance response."""
    asset: str
    free: float
    locked: float
    total: float
    usd_value: float


class BalancesResponse(BaseModel):
    """Schema for multiple balances."""
    balances: List[BalanceResponse]


# Summary schemas

class PortfolioSummaryResponse(BaseModel):
    """Schema for portfolio summary."""
    portfolio_id: int
    cash_balance: float
    invested_value: float
    total_value: float
    total_pnl: float
    total_pnl_percentage: float
    unrealized_pnl: float
    updated_at: str

