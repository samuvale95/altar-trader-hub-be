"""
Configuration settings for the trading bot backend.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator, field_validator
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Altar Trader Hub Backend"
    version: str = "0.1.0"
    debug: bool = True
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./trading_bot.db"
    redis_url: Optional[str] = None  # Redis is optional now
    
    # Security
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 ore
    refresh_token_expire_days: int = 7
    
    # CORS
    allowed_origins: List[str] = ["*"]
    
    # Exchange API Keys
    binance_api_key: Optional[str] = None
    binance_secret_key: Optional[str] = None
    binance_testnet: bool = True
    
    kraken_api_key: Optional[str] = None
    kraken_secret_key: Optional[str] = None
    kraken_sandbox: bool = True
    
    kucoin_api_key: Optional[str] = None
    kucoin_secret_key: Optional[str] = None
    kucoin_passphrase: Optional[str] = None
    kucoin_sandbox: bool = True
    
    # Notification Services
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/1"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Data Feeder
    data_feeder_interval: int = 60
    max_candles_per_request: int = 1000
    
    # Strategy Engine
    strategy_execution_interval: int = 30
    max_concurrent_strategies: int = 10
    
    # Monitoring
    prometheus_port: int = 9090
    health_check_interval: int = 30
    
    # Scheduler Backend
    scheduler_backend: str = "apscheduler"  # Options: "apscheduler" or "celery"
    
    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v):
        # Heroku provides postgres:// but SQLAlchemy needs postgresql://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        
        if not v.startswith(("postgresql://", "postgresql+psycopg2://", "sqlite:///")):
            raise ValueError("Database URL must be a PostgreSQL or SQLite connection string")
        return v
    
    @validator("redis_url")
    def validate_redis_url(cls, v):
        if v is None:
            return None
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
