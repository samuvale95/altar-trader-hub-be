"""
Database configuration and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from app.core.config import settings

# Database Engine (SQLite for development, PostgreSQL for production)
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=settings.debug
    )
else:
    engine = create_engine(
        settings.database_url,
        poolclass=StaticPool,
        pool_pre_ping=True,
        echo=settings.debug
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Redis connection
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """Dependency to get Redis client."""
    return redis_client


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def close_db():
    """Close database connections."""
    engine.dispose()
