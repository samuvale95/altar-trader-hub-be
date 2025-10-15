"""
Schemas for data collection configuration and execution logs.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class DataCollectionConfigBase(BaseModel):
    """Base schema for data collection configuration."""
    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USDT)")
    exchange: str = Field(default="binance", description="Exchange name")
    timeframes: List[str] = Field(..., description="List of timeframes to collect (e.g., ['1m', '5m', '1h'])")
    interval_minutes: int = Field(default=10, ge=1, le=1440, description="Collection interval in minutes")
    enabled: bool = Field(default=True, description="Whether collection is enabled")
    description: Optional[str] = Field(None, max_length=200, description="Optional description")
    
    @validator('timeframes')
    def validate_timeframes(cls, v):
        valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        for tf in v:
            if tf not in valid_timeframes:
                raise ValueError(f"Invalid timeframe: {tf}. Must be one of {valid_timeframes}")
        return v
    
    @validator('symbol')
    def validate_symbol(cls, v):
        # Basic validation: should contain /
        if '/' not in v:
            raise ValueError("Symbol must be in format BASE/QUOTE (e.g., BTC/USDT)")
        return v.upper()


class DataCollectionConfigCreate(DataCollectionConfigBase):
    """Schema for creating a new data collection configuration."""
    pass


class DataCollectionConfigUpdate(BaseModel):
    """Schema for updating data collection configuration."""
    timeframes: Optional[List[str]] = None
    interval_minutes: Optional[int] = Field(None, ge=1, le=1440)
    enabled: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=200)
    
    @validator('timeframes')
    def validate_timeframes(cls, v):
        if v is None:
            return v
        valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        for tf in v:
            if tf not in valid_timeframes:
                raise ValueError(f"Invalid timeframe: {tf}")
        return v


class DataCollectionConfig(DataCollectionConfigBase):
    """Schema for data collection configuration response."""
    id: int
    job_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]
    
    class Config:
        from_attributes = True


class JobExecutionLogBase(BaseModel):
    """Base schema for job execution log."""
    job_name: str
    job_type: str
    symbol: Optional[str] = None
    exchange: Optional[str] = None
    timeframe: Optional[str] = None


class JobExecutionLogCreate(JobExecutionLogBase):
    """Schema for creating a job execution log."""
    metadata: Optional[Dict[str, Any]] = None


class JobExecutionLog(JobExecutionLogBase):
    """Schema for job execution log response."""
    id: int
    started_at: datetime
    finished_at: Optional[datetime]
    duration_seconds: Optional[float]
    status: str
    records_collected: Optional[int]
    error_message: Optional[str]
    error_type: Optional[str]
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class JobExecutionStats(BaseModel):
    """Statistics about job executions."""
    total_executions: int
    successful_executions: int
    failed_executions: int
    running_executions: int
    success_rate: float
    average_duration_seconds: Optional[float]
    total_records_collected: Optional[int]
    last_execution: Optional[datetime]


class DataCollectionStatus(BaseModel):
    """Overall status of data collection."""
    total_configs: int
    enabled_configs: int
    disabled_configs: int
    active_jobs: int
    recent_executions: List[JobExecutionLog]
    stats: JobExecutionStats

