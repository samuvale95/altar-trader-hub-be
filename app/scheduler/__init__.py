"""
Scheduler module for background tasks.

Supports multiple backends:
- APScheduler (default) - runs in the web dyno
- Celery - requires separate worker dyno

Switch via SCHEDULER_BACKEND environment variable.
"""

from app.scheduler.factory import get_scheduler, start_scheduler, shutdown_scheduler
from app.scheduler.manager import (
    add_strategy_job,
    remove_strategy_job,
    update_strategy_job,
    reload_active_strategies
)

__all__ = [
    'get_scheduler',
    'start_scheduler',
    'shutdown_scheduler',
    'add_strategy_job',
    'remove_strategy_job',
    'update_strategy_job',
    'reload_active_strategies',
]

