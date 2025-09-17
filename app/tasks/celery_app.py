"""
Celery application configuration.
"""

from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "trading_bot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.data_feeding",
        "app.tasks.strategy_tasks",
        "app.tasks.cleanup",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    beat_schedule={
        "data-feeding": {
            "task": "app.tasks.data_feeding.collect_market_data",
            "schedule": settings.data_feeder_interval,
        },
        "strategy-execution": {
            "task": "app.tasks.strategy_tasks.execute_strategies",
            "schedule": settings.strategy_execution_interval,
        },
        "cleanup-old-data": {
            "task": "app.tasks.cleanup.cleanup_old_data",
            "schedule": 86400,  # Daily
        },
        "sync-balances": {
            "task": "app.tasks.data_feeding.sync_balances",
            "schedule": 300,  # Every 5 minutes
        },
        "update-positions": {
            "task": "app.tasks.data_feeding.update_positions",
            "schedule": 60,  # Every minute
        },
    },
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.data_feeding.*": {"queue": "data_feeder"},
    "app.tasks.strategy_tasks.*": {"queue": "strategy_engine"},
    "app.tasks.cleanup.*": {"queue": "maintenance"},
}
