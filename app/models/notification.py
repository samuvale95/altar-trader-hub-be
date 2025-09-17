"""
Notification-related database models.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class NotificationType(str, enum.Enum):
    """Notification type enumeration."""
    EMAIL = "email"
    PUSH = "push"
    TELEGRAM = "telegram"
    WEBSOCKET = "websocket"
    SMS = "sms"


class NotificationStatus(str, enum.Enum):
    """Notification status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority(str, enum.Enum):
    """Notification priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """Notification model for user notifications."""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True)
    
    # Notification details
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Status and delivery
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    sent_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    failure_reason = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Delivery details
    recipient = Column(String(255))  # Email, phone, chat ID, etc.
    delivery_method = Column(String(50))  # SMTP, FCM, Telegram API, etc.
    external_id = Column(String(100))  # External service message ID
    
    # Content and context
    data = Column(JSON)  # Additional data for template rendering
    metadata = Column(JSON)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    scheduled_at = Column(DateTime(timezone=True))  # For scheduled notifications
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    template = relationship("NotificationTemplate", back_populates="notifications")


class NotificationTemplate(Base):
    """Notification template model for reusable notification templates."""
    
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    
    # Template content
    type = Column(Enum(NotificationType), nullable=False)
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)
    
    # Template variables
    variables = Column(JSON)  # List of required variables
    default_values = Column(JSON)  # Default values for variables
    
    # Template settings
    is_active = Column(Boolean, default=True)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Delivery settings
    delivery_methods = Column(JSON)  # List of supported delivery methods
    rate_limit = Column(Integer, default=10)  # Max notifications per hour
    cooldown_period = Column(Integer, default=300)  # Cooldown in seconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    notifications = relationship("Notification", back_populates="template")
