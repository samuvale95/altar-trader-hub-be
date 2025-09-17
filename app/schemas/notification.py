"""
Notification-related Pydantic schemas.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, validator
from app.models.notification import NotificationType, NotificationStatus, NotificationPriority


# Notification schemas
class NotificationBase(BaseModel):
    """Base notification schema."""
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    recipient: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    """Schema for notification creation."""
    template_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    max_retries: int = 3


class NotificationResponse(NotificationBase):
    """Schema for notification responses."""
    id: int
    user_id: int
    template_id: Optional[int] = None
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    retry_count: int
    max_retries: int
    delivery_method: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Notification template schemas
class NotificationTemplateBase(BaseModel):
    """Base notification template schema."""
    name: str
    description: Optional[str] = None
    type: NotificationType
    title_template: str
    message_template: str
    variables: Optional[List[str]] = None
    default_values: Optional[Dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    delivery_methods: Optional[List[str]] = None
    rate_limit: int = 10
    cooldown_period: int = 300


class NotificationTemplateCreate(NotificationTemplateBase):
    """Schema for notification template creation."""
    pass


class NotificationTemplateUpdate(BaseModel):
    """Schema for notification template updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    title_template: Optional[str] = None
    message_template: Optional[str] = None
    variables: Optional[List[str]] = None
    default_values: Optional[Dict[str, Any]] = None
    priority: Optional[NotificationPriority] = None
    delivery_methods: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    cooldown_period: Optional[int] = None
    is_active: Optional[bool] = None


class NotificationTemplateResponse(NotificationTemplateBase):
    """Schema for notification template responses."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Notification preferences schemas
class NotificationPreferences(BaseModel):
    """Schema for notification preferences."""
    email_enabled: bool = True
    push_enabled: bool = True
    telegram_enabled: bool = False
    sms_enabled: bool = False
    websocket_enabled: bool = True
    
    # Email preferences
    email_address: Optional[str] = None
    
    # Telegram preferences
    telegram_chat_id: Optional[str] = None
    
    # SMS preferences
    phone_number: Optional[str] = None
    
    # Notification types
    trade_notifications: bool = True
    price_alerts: bool = True
    strategy_signals: bool = True
    system_alerts: bool = True
    news_alerts: bool = False
    
    # Frequency settings
    immediate_notifications: bool = True
    daily_summary: bool = True
    weekly_report: bool = True


# Notification filtering schemas
class NotificationFilter(BaseModel):
    """Schema for notification filtering."""
    type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    priority: Optional[NotificationPriority] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


# Notification statistics schemas
class NotificationStats(BaseModel):
    """Schema for notification statistics."""
    total_notifications: int
    sent_notifications: int
    failed_notifications: int
    pending_notifications: int
    success_rate: Decimal
    avg_delivery_time: Optional[Decimal] = None
    most_common_type: Optional[str] = None
    most_common_failure_reason: Optional[str] = None


# WebSocket notification schemas
class WebSocketNotification(BaseModel):
    """Schema for WebSocket notifications."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    user_id: int


# Alert schemas
class PriceAlert(BaseModel):
    """Schema for price alerts."""
    symbol: str
    condition: str  # above, below, equals
    target_price: Decimal
    is_active: bool = True
    expires_at: Optional[datetime] = None
    
    @validator('condition')
    def validate_condition(cls, v):
        allowed_conditions = ['above', 'below', 'equals']
        if v.lower() not in allowed_conditions:
            raise ValueError(f'Condition must be one of: {allowed_conditions}')
        return v.lower()


class StrategyAlert(BaseModel):
    """Schema for strategy alerts."""
    strategy_id: int
    alert_type: str  # signal, execution, performance, error
    threshold: Optional[Decimal] = None
    is_active: bool = True
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        allowed_types = ['signal', 'execution', 'performance', 'error']
        if v.lower() not in allowed_types:
            raise ValueError(f'Alert type must be one of: {allowed_types}')
        return v.lower()
