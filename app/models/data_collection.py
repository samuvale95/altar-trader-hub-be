"""
Models for data collection configuration and execution tracking.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, Text
from sqlalchemy.sql import func
from app.core.database import Base


class DataCollectionConfig(Base):
    """
    Configuration for automated data collection.
    
    Each record defines what data to collect and how often.
    """
    __tablename__ = "data_collection_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # What to collect
    symbol = Column(String(20), nullable=False, index=True)  # e.g., "BTC/USDT"
    exchange = Column(String(20), nullable=False, default="binance")  # e.g., "binance"
    timeframes = Column(JSON, nullable=False)  # e.g., ["1m", "5m", "1h"]
    
    # When to collect
    interval_minutes = Column(Integer, nullable=False, default=10)  # Collection frequency
    
    # Status
    enabled = Column(Boolean, default=True, index=True)
    
    # Metadata
    job_id = Column(String(100), unique=True, nullable=True)  # APScheduler job ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Notes
    description = Column(String(200), nullable=True)
    created_by = Column(Integer, nullable=True)  # User ID
    
    def __repr__(self):
        return f"<DataCollectionConfig {self.symbol} on {self.exchange}>"


class JobExecutionLog(Base):
    """
    Log of all job executions.
    
    Tracks start time, end time, success/failure, and details.
    """
    __tablename__ = "job_execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Job identification
    job_name = Column(String(100), nullable=False, index=True)  # e.g., "collect_crypto_data"
    job_type = Column(String(50), nullable=False, index=True)  # e.g., "data_collection", "cleanup", "strategy"
    
    # Execution details
    symbol = Column(String(20), nullable=True, index=True)  # If specific to a symbol
    exchange = Column(String(20), nullable=True)
    timeframe = Column(String(10), nullable=True)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)  # Auto-calculated
    
    # Result
    status = Column(String(20), nullable=False, default="running", index=True)  # running, success, failed, timeout
    records_collected = Column(Integer, nullable=True)  # Number of records collected/processed
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)  # Any additional info
    
    def __repr__(self):
        return f"<JobExecutionLog {self.job_name} at {self.started_at}>"

