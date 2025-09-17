"""
Logging configuration for the trading bot backend.
"""

import logging
import sys
from typing import Any, Dict
import structlog
from app.core.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class TradingLogger:
    """Custom logger for trading operations."""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def log_trade(self, trade_data: Dict[str, Any]) -> None:
        """Log trade execution."""
        self.logger.info("Trade executed", **trade_data)
    
    def log_strategy_signal(self, signal_data: Dict[str, Any]) -> None:
        """Log strategy signal."""
        self.logger.info("Strategy signal generated", **signal_data)
    
    def log_order_update(self, order_data: Dict[str, Any]) -> None:
        """Log order status update."""
        self.logger.info("Order status updated", **order_data)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Log error with context."""
        self.logger.error(
            "Error occurred",
            error=str(error),
            error_type=type(error).__name__,
            **(context or {})
        )
    
    def log_performance(self, performance_data: Dict[str, Any]) -> None:
        """Log strategy performance metrics."""
        self.logger.info("Performance metrics", **performance_data)
