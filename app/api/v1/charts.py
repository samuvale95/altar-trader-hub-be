"""
Charts API endpoints for market data visualization.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.market_data import MarketData
from app.core.logging import get_logger
from app.services.chart_service import ChartService
from app.schemas.market_data import (
    ChartData, ChartDataPoint, PriceHistory, PriceHistoryPoint,
    VolumeData, VolumeDataPoint, TechnicalIndicatorData, TechnicalIndicatorPoint,
    ChartSummary, SymbolInfo, TimeframeInfo, AvailableSymbolsResponse,
    AvailableTimeframesResponse, ChartRequest
)
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

router = APIRouter()
logger = get_logger(__name__)


# ============================================================================
# CANDLESTICK CHARTS
# ============================================================================

@router.get("/candlestick/{symbol}", response_model=ChartData)
def get_candlestick_data(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w"),
    limit: int = Query(1000, description="Number of candles to return (max 2000)"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get candlestick data for a symbol."""
    
    try:
        chart_service = ChartService(db)
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        return chart_service.get_candlestick_data(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            start_date=start_dt,
            end_date=end_dt
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting candlestick data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candlestick data: {str(e)}"
        )


# ============================================================================
# PRICE HISTORY CHARTS
# ============================================================================

@router.get("/price-history/{symbol}", response_model=PriceHistory)
def get_price_history(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w"),
    limit: int = Query(1000, description="Number of data points to return (max 2000)"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get price history for a symbol."""
    
    try:
        chart_service = ChartService(db)
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        return chart_service.get_price_history(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            start_date=start_dt,
            end_date=end_dt
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting price history for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get price history: {str(e)}"
        )


# ============================================================================
# VOLUME CHARTS
# ============================================================================

@router.get("/volume/{symbol}", response_model=VolumeData)
def get_volume_data(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w"),
    limit: int = Query(1000, description="Number of data points to return (max 2000)"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get volume data for a symbol."""
    
    try:
        chart_service = ChartService(db)
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        return chart_service.get_volume_data(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            start_date=start_dt,
            end_date=end_dt
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting volume data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get volume data: {str(e)}"
        )


# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================

@router.get("/indicators/{symbol}/{indicator_name}", response_model=TechnicalIndicatorData)
def get_technical_indicator(
    symbol: str,
    indicator_name: str,
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w"),
    limit: int = Query(1000, description="Number of data points to return (max 2000)"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get technical indicator data for a symbol."""
    
    try:
        chart_service = ChartService(db)
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        return chart_service.get_technical_indicator(
            symbol=symbol,
            timeframe=timeframe,
            indicator_name=indicator_name,
            limit=limit,
            start_date=start_dt,
            end_date=end_dt
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting technical indicator for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get technical indicator: {str(e)}"
        )


@router.get("/indicators/{symbol}/all", response_model=Dict[str, TechnicalIndicatorData])
def get_all_technical_indicators(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w"),
    limit: int = Query(1000, description="Number of data points to return (max 2000)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all technical indicators for a symbol."""
    
    try:
        chart_service = ChartService(db)
        
        return chart_service.calculate_technical_indicators(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error calculating technical indicators for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate technical indicators: {str(e)}"
        )


# ============================================================================
# CHART SUMMARY
# ============================================================================

@router.get("/summary/{symbol}", response_model=ChartSummary)
def get_chart_summary(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chart summary data for a symbol."""
    
    try:
        chart_service = ChartService(db)
        
        return chart_service.get_chart_summary(
            symbol=symbol,
            timeframe=timeframe
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting chart summary for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chart summary: {str(e)}"
        )


# ============================================================================
# AVAILABLE SYMBOLS AND TIMEFRAMES
# ============================================================================

@router.get("/available-symbols", response_model=AvailableSymbolsResponse)
def get_available_symbols(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available symbols with data."""
    
    try:
        chart_service = ChartService(db)
        symbols = chart_service.get_available_symbols()
        
        return AvailableSymbolsResponse(
            symbols=symbols,
            total_symbols=len(symbols)
        )
        
    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available symbols: {str(e)}"
        )


@router.get("/timeframes/{symbol}", response_model=AvailableTimeframesResponse)
def get_available_timeframes(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available timeframes for a symbol."""
    
    try:
        chart_service = ChartService(db)
        timeframes = chart_service.get_available_timeframes(symbol)
        
        return AvailableTimeframesResponse(
            symbol=symbol.upper(),
            timeframes=timeframes,
            total_timeframes=len(timeframes)
        )
        
    except Exception as e:
        logger.error(f"Error getting timeframes for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timeframes: {str(e)}"
        )


# ============================================================================
# COMPREHENSIVE CHART DATA
# ============================================================================

@router.post("/comprehensive/{symbol}", response_model=Dict[str, Any])
def get_comprehensive_chart_data(
    symbol: str,
    chart_request: ChartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive chart data including OHLCV and technical indicators."""
    
    try:
        chart_service = ChartService(db)
        
        # Get candlestick data
        candlestick_data = chart_service.get_candlestick_data(
            symbol=symbol,
            timeframe=chart_request.timeframe,
            limit=chart_request.limit,
            start_date=chart_request.start_date,
            end_date=chart_request.end_date
        )
        
        # Get volume data
        volume_data = chart_service.get_volume_data(
            symbol=symbol,
            timeframe=chart_request.timeframe,
            limit=chart_request.limit,
            start_date=chart_request.start_date,
            end_date=chart_request.end_date
        )
        
        # Get chart summary
        summary = chart_service.get_chart_summary(
            symbol=symbol,
            timeframe=chart_request.timeframe
        )
        
        # Get technical indicators if requested
        indicators = {}
        if chart_request.indicators:
            for indicator_name in chart_request.indicators:
                try:
                    indicators[indicator_name] = chart_service.get_technical_indicator(
                        symbol=symbol,
                        timeframe=chart_request.timeframe,
                        indicator_name=indicator_name,
                        limit=chart_request.limit,
                        start_date=chart_request.start_date,
                        end_date=chart_request.end_date
                    )
                except Exception as e:
                    logger.warning(f"Failed to get indicator {indicator_name}: {e}")
                    continue
        
        return {
            "candlestick": candlestick_data,
            "volume": volume_data,
            "summary": summary,
            "indicators": indicators,
            "metadata": {
                "symbol": symbol.upper(),
                "timeframe": chart_request.timeframe,
                "requested_indicators": chart_request.indicators or [],
                "available_indicators": list(indicators.keys()),
                "data_points": candlestick_data.count
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting comprehensive chart data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comprehensive chart data: {str(e)}"
        )

