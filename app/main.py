"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import structlog
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.database import init_db
from app.api.v1 import auth, portfolio, strategies, orders, market_data, websocket, notifications, trading_strategies, trading_monitor, symbols, system, strategy_control, data_collector, charts, cronjob_manager

# Configure logging
configure_logging()
logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Backend for Altar Trader Hub - Crypto Trading Bot",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error("Internal server error", error=str(exc), url=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.version,
        "environment": settings.environment,
        "timestamp": time.time()
    }

# Include API routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

app.include_router(
    portfolio.router,
    prefix="/api/v1/portfolio",
    tags=["portfolio"]
)

app.include_router(
    strategies.router,
    prefix="/api/v1/strategies",
    tags=["strategies"]
)

app.include_router(
    orders.router,
    prefix="/api/v1/orders",
    tags=["orders"]
)

app.include_router(
    market_data.router,
    prefix="/api/v1/market-data",
    tags=["market-data"]
)

app.include_router(
    websocket.router,
    prefix="/ws",
    tags=["websocket"]
)

app.include_router(
    notifications.router,
    prefix="/api/v1/notifications",
    tags=["notifications"]
)

app.include_router(
    trading_strategies.router,
    prefix="/api/v1/trading-strategies",
    tags=["trading-strategies"]
)

app.include_router(
    trading_monitor.router,
    prefix="/api/v1/trading-monitor",
    tags=["trading-monitor"]
)

app.include_router(
    symbols.router,
    prefix="/api/v1/symbols",
    tags=["symbols"]
)

app.include_router(
    system.router,
    prefix="/api/v1/system",
    tags=["system"]
)

app.include_router(
    strategy_control.router,
    prefix="/api/v1/strategy-control",
    tags=["strategy-control"]
)

app.include_router(
    data_collector.router,
    prefix="/api/v1/data-collector",
    tags=["data-collector"]
)

app.include_router(
    charts.router,
    prefix="/api/v1/charts",
    tags=["charts"]
)

app.include_router(
    cronjob_manager.router,
    prefix="/api/v1/cronjob",
    tags=["cronjob-manager"]
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting application", version=settings.version)
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Start data collection scheduler
    from app.services.data_scheduler import data_scheduler
    await data_scheduler.start_scheduler()
    logger.info("Data collection scheduler started")
    
    # Initialize task manager
    from app.services.task_manager import task_manager
    logger.info("Task manager initialized")
    
    # TODO: Initialize Redis connection
    # TODO: Initialize Celery workers
    # TODO: Start background tasks
    
    logger.info("Application startup completed")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application")
    
    # Stop data collection scheduler
    from app.services.data_scheduler import data_scheduler
    await data_scheduler.stop_scheduler()
    logger.info("Data collection scheduler stopped")
    
    # Shutdown task manager
    from app.services.task_manager import task_manager
    await task_manager.shutdown()
    logger.info("Task manager shutdown completed")
    
    # TODO: Close database connections
    # TODO: Stop background tasks
    # TODO: Cleanup resources
    
    logger.info("Application shutdown completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
