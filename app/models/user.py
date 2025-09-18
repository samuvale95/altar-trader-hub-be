"""
User-related database models.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    trading_strategies = relationship("TradingStrategy", back_populates="user", cascade="all, delete-orphan")


class APIKey(Base):
    """Exchange API keys for user accounts."""
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exchange = Column(String(50), nullable=False)  # binance, kraken, kucoin
    api_key = Column(String(255), nullable=False)
    secret_key = Column(String(255), nullable=False)
    passphrase = Column(String(255))  # For KuCoin
    is_active = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class UserPreferences(Base):
    """User preferences and settings."""
    
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    telegram_notifications = Column(Boolean, default=False)
    
    # Trading preferences
    default_risk_per_trade = Column(String(10), default="1%")  # 1%, 2%, 5%
    max_concurrent_strategies = Column(Integer, default=5)
    auto_trade_enabled = Column(Boolean, default=False)
    
    # UI preferences
    theme = Column(String(20), default="dark")  # dark, light
    language = Column(String(5), default="en")  # en, it, es, fr
    timezone = Column(String(50), default="UTC")
    
    # Risk management
    max_daily_loss = Column(String(10), default="5%")
    max_position_size = Column(String(10), default="10%")
    stop_loss_enabled = Column(Boolean, default=True)
    take_profit_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
