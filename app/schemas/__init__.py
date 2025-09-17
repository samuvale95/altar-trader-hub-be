"""
Pydantic schemas for API request/response models.
"""

from .user import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    APIKeyCreate, APIKeyUpdate, APIKeyResponse,
    UserPreferencesCreate, UserPreferencesUpdate, UserPreferencesResponse
)
from .portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    PositionCreate, PositionUpdate, PositionResponse,
    BalanceResponse
)
from .strategy import (
    StrategyCreate, StrategyUpdate, StrategyResponse,
    StrategySignalResponse, StrategyPerformanceResponse
)
from .order import (
    OrderCreate, OrderUpdate, OrderResponse,
    TradeResponse
)
from .market_data import (
    MarketDataResponse, NewsResponse, IndicatorResponse
)
from .notification import (
    NotificationCreate, NotificationResponse,
    NotificationTemplateCreate, NotificationTemplateResponse
)

__all__ = [
    # User schemas
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "APIKeyCreate", "APIKeyUpdate", "APIKeyResponse",
    "UserPreferencesCreate", "UserPreferencesUpdate", "UserPreferencesResponse",
    
    # Portfolio schemas
    "PortfolioCreate", "PortfolioUpdate", "PortfolioResponse",
    "PositionCreate", "PositionUpdate", "PositionResponse",
    "BalanceResponse",
    
    # Strategy schemas
    "StrategyCreate", "StrategyUpdate", "StrategyResponse",
    "StrategySignalResponse", "StrategyPerformanceResponse",
    
    # Order schemas
    "OrderCreate", "OrderUpdate", "OrderResponse",
    "TradeResponse",
    
    # Market data schemas
    "MarketDataResponse", "NewsResponse", "IndicatorResponse",
    
    # Notification schemas
    "NotificationCreate", "NotificationResponse",
    "NotificationTemplateCreate", "NotificationTemplateResponse",
]
