"""
User-related Pydantic schemas.
"""

from typing import Optional, List, Annotated, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator, field_validator, BeforeValidator
from enum import Enum


class TradingModeEnum(str, Enum):
    """Trading mode enumeration for schemas."""
    PAPER = "paper"
    LIVE = "live"


def normalize_trading_mode(value: Any) -> str:
    """Normalize trading mode to lowercase."""
    if isinstance(value, str):
        return value.lower()
    return value


# Type alias for trading mode with automatic normalization
NormalizedTradingMode = Annotated[TradingModeEnum, BeforeValidator(normalize_trading_mode)]


# Base schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str
    trading_mode: Optional[str] = "paper"
    
    @field_validator('trading_mode', mode='before')
    @classmethod
    def normalize_and_validate_trading_mode(cls, v):
        """Normalize trading mode to lowercase and validate."""
        if v is None:
            return "paper"
        if isinstance(v, str):
            v = v.lower()
            if v not in ["paper", "live"]:
                raise ValueError("trading_mode must be 'paper' or 'live'")
            return v
        raise ValueError("trading_mode must be a string")


class UserResponse(UserBase):
    """Schema for user responses."""
    id: int
    is_active: bool
    is_verified: bool
    trading_mode: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# API Key schemas
class APIKeyBase(BaseModel):
    """Base API key schema."""
    exchange: str
    is_sandbox: bool = True


class APIKeyCreate(APIKeyBase):
    """Schema for API key creation."""
    api_key: str
    secret_key: str
    passphrase: Optional[str] = None
    
    @validator('exchange')
    def validate_exchange(cls, v):
        allowed_exchanges = ['binance', 'kraken', 'kucoin']
        if v.lower() not in allowed_exchanges:
            raise ValueError(f'Exchange must be one of: {allowed_exchanges}')
        return v.lower()


class APIKeyUpdate(BaseModel):
    """Schema for API key updates."""
    is_active: Optional[bool] = None
    is_sandbox: Optional[bool] = None


class APIKeyResponse(APIKeyBase):
    """Schema for API key responses."""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# User Preferences schemas
class UserPreferencesBase(BaseModel):
    """Base user preferences schema."""
    email_notifications: bool = True
    push_notifications: bool = True
    telegram_notifications: bool = False
    default_risk_per_trade: str = "1%"
    max_concurrent_strategies: int = 5
    auto_trade_enabled: bool = False
    theme: str = "dark"
    language: str = "en"
    timezone: str = "UTC"
    max_daily_loss: str = "5%"
    max_position_size: str = "10%"
    stop_loss_enabled: bool = True
    take_profit_enabled: bool = True


class UserPreferencesCreate(UserPreferencesBase):
    """Schema for user preferences creation."""
    pass


class UserPreferencesUpdate(BaseModel):
    """Schema for user preferences updates."""
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    telegram_notifications: Optional[bool] = None
    default_risk_per_trade: Optional[str] = None
    max_concurrent_strategies: Optional[int] = None
    auto_trade_enabled: Optional[bool] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    max_daily_loss: Optional[str] = None
    max_position_size: Optional[str] = None
    stop_loss_enabled: Optional[bool] = None
    take_profit_enabled: Optional[bool] = None


class UserPreferencesResponse(UserPreferencesBase):
    """Schema for user preferences responses."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    """Schema for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    trading_mode: str


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: Optional[int] = None
    trading_mode: Optional[str] = "paper"
