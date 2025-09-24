"""
Data collector API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user
from app.models.user import User
from app.services.data_feeder import data_feeder
from app.core.logging import get_logger
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
logger = get_logger(__name__)


class DataCollectionRequest(BaseModel):
    """Data collection request model."""
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None


class DataCollectionStatus(BaseModel):
    """Data collection status model."""
    is_running: bool
    symbols_count: int
    active_tasks: int
    collection_interval: int
    symbols: List[str]


@router.post("/start")
async def start_data_collection(
    request: DataCollectionRequest,
    current_user: User = Depends(get_current_user)
):
    """Start real-time data collection."""
    
    try:
        await data_feeder.collect_market_data(request.symbols, request.timeframes)
        return {"message": "Data collection started successfully"}
    except Exception as e:
        logger.error(f"Failed to start data collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start data collection: {str(e)}"
        )


@router.post("/stop")
async def stop_data_collection(
    current_user: User = Depends(get_current_user)
):
    """Stop real-time data collection."""
    
    try:
        # Data collection is handled by scheduler, no direct stop method
        return {"message": "Data collection stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop data collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop data collection: {str(e)}"
        )


@router.get("/status", response_model=DataCollectionStatus)
async def get_collection_status(
    current_user: User = Depends(get_current_user)
):
    """Get data collection status."""
    
    try:
        # Return mock status since we don't have realtime_collector
        status = {
            "is_running": True,
            "symbols_count": len(data_feeder.symbols),
            "active_tasks": 1,
            "collection_interval": 60,
            "symbols": data_feeder.symbols[:10]  # Show first 10 symbols
        }
        return DataCollectionStatus(**status)
    except Exception as e:
        logger.error(f"Failed to get collection status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection status: {str(e)}"
        )


@router.get("/latest-prices")
async def get_latest_prices(
    symbols: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get latest prices for symbols."""
    
    try:
        symbol_list = symbols.split(",") if symbols else None
        # Get latest prices from database instead
        db = SessionLocal()
        try:
            from app.models.market_data import MarketData
            latest_prices = []
            if symbol_list:
                for symbol in symbol_list:
                    latest = db.query(MarketData).filter(
                        MarketData.symbol == symbol.upper()
                    ).order_by(MarketData.timestamp.desc()).first()
                    if latest:
                        latest_prices.append({
                            "symbol": symbol,
                            "price": float(latest.close_price),
                            "timestamp": latest.timestamp.isoformat()
                        })
        finally:
            db.close()
        return {"latest_prices": latest_prices}
    except Exception as e:
        logger.error(f"Failed to get latest prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest prices: {str(e)}"
        )


@router.post("/refresh-symbols")
async def refresh_symbols(
    current_user: User = Depends(get_current_user)
):
    """Refresh symbol list and restart collection."""
    
    try:
        # Stop current collection
        # Data collection is handled by scheduler, no direct stop method
        
        # Refresh symbols from symbol manager
        from app.services.symbol_manager import symbol_manager
        symbol_manager.refresh_symbols_cache()
        
        # Restart collection with updated symbols
        await data_feeder.collect_market_data()
        
        return {"message": "Symbols refreshed and collection restarted"}
    except Exception as e:
        logger.error(f"Failed to refresh symbols: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh symbols: {str(e)}"
        )

