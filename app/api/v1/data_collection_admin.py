"""
API endpoints for managing data collection configurations.

Allows dynamic management of what data to collect and when.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.data_collection import DataCollectionConfig, JobExecutionLog
from app.schemas.data_collection import (
    DataCollectionConfigCreate,
    DataCollectionConfigUpdate,
    DataCollectionConfig as DataCollectionConfigSchema,
    JobExecutionLog as JobExecutionLogSchema,
    JobExecutionStats,
    DataCollectionStatus
)

router = APIRouter()


@router.get("/configs", response_model=List[DataCollectionConfigSchema])
async def list_data_collection_configs(
    enabled: Optional[bool] = None,
    exchange: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all data collection configurations.
    
    Optionally filter by enabled status or exchange.
    """
    query = db.query(DataCollectionConfig)
    
    if enabled is not None:
        query = query.filter(DataCollectionConfig.enabled == enabled)
    
    if exchange:
        query = query.filter(DataCollectionConfig.exchange == exchange)
    
    configs = query.offset(skip).limit(limit).all()
    return configs


@router.post("/configs", response_model=DataCollectionConfigSchema, status_code=201)
async def create_data_collection_config(
    config: DataCollectionConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new data collection configuration.
    
    This will automatically start collecting data for the specified symbol.
    """
    # Check if config already exists for this symbol/exchange
    existing = db.query(DataCollectionConfig).filter(
        DataCollectionConfig.symbol == config.symbol,
        DataCollectionConfig.exchange == config.exchange
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Configuration already exists for {config.symbol} on {config.exchange}"
        )
    
    # Create config
    db_config = DataCollectionConfig(
        **config.dict(),
        created_by=current_user.id,
        job_id=f"collect_{config.symbol.replace('/', '_')}_{config.exchange}"
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    # Add scheduler job if enabled
    if db_config.enabled:
        from app.scheduler.manager import add_data_collection_job
        add_data_collection_job(db_config.id)
    
    return db_config


@router.get("/configs/{config_id}", response_model=DataCollectionConfigSchema)
async def get_data_collection_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific data collection configuration."""
    config = db.query(DataCollectionConfig).filter(
        DataCollectionConfig.id == config_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return config


@router.put("/configs/{config_id}", response_model=DataCollectionConfigSchema)
async def update_data_collection_config(
    config_id: int,
    config_update: DataCollectionConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a data collection configuration.
    
    This will automatically update the scheduled job.
    """
    db_config = db.query(DataCollectionConfig).filter(
        DataCollectionConfig.id == config_id
    ).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Update fields
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    
    # Update scheduler job
    from app.scheduler.manager import update_data_collection_job, remove_data_collection_job, add_data_collection_job
    
    if db_config.enabled:
        # Update or recreate job
        success = update_data_collection_job(db_config.id)
        if not success:
            # Recreate job if update failed
            add_data_collection_job(db_config.id)
    else:
        # Remove job if disabled
        remove_data_collection_job(db_config.id)
    
    return db_config


@router.delete("/configs/{config_id}", status_code=204)
async def delete_data_collection_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a data collection configuration.
    
    This will stop collecting data for this symbol.
    """
    db_config = db.query(DataCollectionConfig).filter(
        DataCollectionConfig.id == config_id
    ).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Remove scheduler job
    from app.scheduler.manager import remove_data_collection_job
    remove_data_collection_job(db_config.id)
    
    # Delete config
    db.delete(db_config)
    db.commit()
    
    return None


@router.post("/configs/{config_id}/enable", response_model=DataCollectionConfigSchema)
async def enable_data_collection_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enable a data collection configuration and start the job."""
    db_config = db.query(DataCollectionConfig).filter(
        DataCollectionConfig.id == config_id
    ).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    db_config.enabled = True
    db.commit()
    db.refresh(db_config)
    
    # Add scheduler job
    from app.scheduler.manager import add_data_collection_job
    add_data_collection_job(db_config.id)
    
    return db_config


@router.post("/configs/{config_id}/disable", response_model=DataCollectionConfigSchema)
async def disable_data_collection_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disable a data collection configuration and stop the job."""
    db_config = db.query(DataCollectionConfig).filter(
        DataCollectionConfig.id == config_id
    ).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    db_config.enabled = False
    db.commit()
    db.refresh(db_config)
    
    # Remove scheduler job
    from app.scheduler.manager import remove_data_collection_job
    remove_data_collection_job(db_config.id)
    
    return db_config


@router.post("/configs/{config_id}/trigger", response_model=dict)
async def trigger_data_collection_now(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger data collection immediately for this configuration.
    
    Does not wait for scheduled time.
    """
    db_config = db.query(DataCollectionConfig).filter(
        DataCollectionConfig.id == config_id
    ).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Trigger collection immediately
    from app.scheduler.manager import trigger_data_collection_now
    import asyncio
    
    asyncio.create_task(trigger_data_collection_now(db_config.id))
    
    return {
        "message": f"Data collection triggered for {db_config.symbol}",
        "config_id": config_id
    }


@router.get("/execution-logs", response_model=List[JobExecutionLogSchema])
async def list_job_execution_logs(
    job_name: Optional[str] = None,
    job_type: Optional[str] = None,
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List job execution logs.
    
    Supports filtering by job name, type, symbol, status, and date range.
    """
    query = db.query(JobExecutionLog).order_by(desc(JobExecutionLog.started_at))
    
    if job_name:
        query = query.filter(JobExecutionLog.job_name == job_name)
    
    if job_type:
        query = query.filter(JobExecutionLog.job_type == job_type)
    
    if symbol:
        query = query.filter(JobExecutionLog.symbol == symbol)
    
    if status:
        query = query.filter(JobExecutionLog.status == status)
    
    if start_date:
        query = query.filter(JobExecutionLog.started_at >= start_date)
    
    if end_date:
        query = query.filter(JobExecutionLog.started_at <= end_date)
    
    logs = query.offset(skip).limit(limit).all()
    return logs


@router.get("/execution-logs/{log_id}", response_model=JobExecutionLogSchema)
async def get_job_execution_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific job execution log."""
    log = db.query(JobExecutionLog).filter(JobExecutionLog.id == log_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return log


@router.get("/stats", response_model=JobExecutionStats)
async def get_job_execution_stats(
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    hours: int = Query(default=24, ge=1, le=720, description="Hours to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about job executions.
    
    Returns success rate, average duration, total records collected, etc.
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = db.query(JobExecutionLog).filter(JobExecutionLog.started_at >= since)
    
    if job_type:
        query = query.filter(JobExecutionLog.job_type == job_type)
    
    logs = query.all()
    
    total_executions = len(logs)
    successful = sum(1 for log in logs if log.status == "success")
    failed = sum(1 for log in logs if log.status == "failed")
    running = sum(1 for log in logs if log.status == "running")
    
    success_rate = (successful / total_executions * 100) if total_executions > 0 else 0
    
    completed_logs = [log for log in logs if log.duration_seconds is not None]
    avg_duration = (
        sum(log.duration_seconds for log in completed_logs) / len(completed_logs)
        if completed_logs else None
    )
    
    total_records = sum(log.records_collected or 0 for log in logs)
    
    last_execution = max((log.started_at for log in logs), default=None)
    
    return JobExecutionStats(
        total_executions=total_executions,
        successful_executions=successful,
        failed_executions=failed,
        running_executions=running,
        success_rate=round(success_rate, 2),
        average_duration_seconds=round(avg_duration, 2) if avg_duration else None,
        total_records_collected=total_records,
        last_execution=last_execution
    )


@router.get("/status", response_model=DataCollectionStatus)
async def get_data_collection_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get overall data collection status.
    
    Returns configuration counts, active jobs, recent executions, and stats.
    """
    # Config stats
    total_configs = db.query(DataCollectionConfig).count()
    enabled_configs = db.query(DataCollectionConfig).filter(
        DataCollectionConfig.enabled == True
    ).count()
    disabled_configs = total_configs - enabled_configs
    
    # Active jobs
    from app.scheduler import get_scheduler
    scheduler = get_scheduler()
    all_jobs = scheduler.get_jobs()
    active_jobs = len([j for j in all_jobs if j.id.startswith("collect_data_")])
    
    # Recent executions (last 10)
    recent_executions = db.query(JobExecutionLog).filter(
        JobExecutionLog.job_type == "data_collection"
    ).order_by(desc(JobExecutionLog.started_at)).limit(10).all()
    
    # Stats (last 24 hours)
    since = datetime.utcnow() - timedelta(hours=24)
    logs = db.query(JobExecutionLog).filter(
        JobExecutionLog.job_type == "data_collection",
        JobExecutionLog.started_at >= since
    ).all()
    
    total_executions = len(logs)
    successful = sum(1 for log in logs if log.status == "success")
    failed = sum(1 for log in logs if log.status == "failed")
    running = sum(1 for log in logs if log.status == "running")
    
    success_rate = (successful / total_executions * 100) if total_executions > 0 else 0
    
    completed_logs = [log for log in logs if log.duration_seconds is not None]
    avg_duration = (
        sum(log.duration_seconds for log in completed_logs) / len(completed_logs)
        if completed_logs else None
    )
    
    total_records = sum(log.records_collected or 0 for log in logs)
    last_execution = max((log.started_at for log in logs), default=None)
    
    stats = JobExecutionStats(
        total_executions=total_executions,
        successful_executions=successful,
        failed_executions=failed,
        running_executions=running,
        success_rate=round(success_rate, 2),
        average_duration_seconds=round(avg_duration, 2) if avg_duration else None,
        total_records_collected=total_records,
        last_execution=last_execution
    )
    
    return DataCollectionStatus(
        total_configs=total_configs,
        enabled_configs=enabled_configs,
        disabled_configs=disabled_configs,
        active_jobs=active_jobs,
        recent_executions=recent_executions,
        stats=stats
    )

