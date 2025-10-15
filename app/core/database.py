"""
Database configuration and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
import redis
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Database Engine (SQLite for development, PostgreSQL for production)
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False  # Disabilita il logging delle query SQL
    )
else:
    # PostgreSQL con connection pooling ottimizzato per Heroku
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=5,  # Numero di connessioni nel pool
        max_overflow=10,  # Connessioni extra oltre pool_size
        pool_pre_ping=True,  # Verifica connessioni prima dell'uso
        pool_recycle=3600,  # Ricrea connessioni dopo 1 ora
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Redis connection (optional)
redis_client: Optional[redis.Redis] = None
if settings.redis_url:
    try:
        redis_client = redis.from_url(
            settings.redis_url, 
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Test connection
        redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Running without Redis cache.")
        redis_client = None
else:
    logger.info("Redis URL not configured. Running without Redis cache.")


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """Dependency to get Redis client."""
    if redis_client is None:
        logger.warning("Redis client not available")
    return redis_client


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def close_db():
    """Close database connections."""
    engine.dispose()
