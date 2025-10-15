"""
Market data API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_optional_current_user
from app.models.user import User
from app.models.market_data import MarketData, News, Indicator
from app.schemas.market_data import (
    MarketDataResponse,
    MarketDataRequest,
    NewsResponse,
    NewsRequest,
    IndicatorResponse,
    IndicatorRequest,
    TickerResponse,
    TickerRequest,
    MarketDataSummary,
    MarketDataStats
)
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/symbols", response_model=List[str])
def get_symbols(
    exchange: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get available trading symbols."""
    
    # Get unique symbols from market data
    query = db.query(MarketData.symbol).distinct()
    
    if exchange:
        # TODO: Filter by exchange when exchange field is added
        pass
    
    symbols = [row[0] for row in query.all()]
    
    return symbols


@router.get("/ohlcv", response_model=List[MarketDataResponse])
def get_ohlcv_data(
    symbol: str,
    timeframe: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """Get OHLCV market data."""
    
    # Validate timeframe
    allowed_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
    if timeframe not in allowed_timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Timeframe must be one of: {allowed_timeframes}"
        )
    
    # Build query
    query = db.query(MarketData).filter(
        MarketData.symbol == symbol,
        MarketData.timeframe == timeframe
    )
    
    # Apply date filters
    if start_date:
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        query = query.filter(MarketData.timestamp >= start_dt)
    
    if end_date:
        from datetime import datetime
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        query = query.filter(MarketData.timestamp <= end_dt)
    
    # Apply limit
    if limit > 1000:
        limit = 1000
    
    # Execute query
    data = query.order_by(MarketData.timestamp.desc()).limit(limit).all()
    
    return data


@router.get("/ticker", response_model=List[TickerResponse])
def get_ticker_data(
    symbols: Optional[str] = None,
    exchange: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get real-time ticker data."""
    
    # Parse symbols
    symbol_list = symbols.split(',') if symbols else []
    
    # Get latest market data for symbols
    query = db.query(MarketData).filter(
        MarketData.timeframe == '1m'  # Use 1-minute data for ticker
    )
    
    if symbol_list:
        query = query.filter(MarketData.symbol.in_(symbol_list))
    
    # Get latest data for each symbol
    latest_data = {}
    for data in query.all():
        if data.symbol not in latest_data or data.timestamp > latest_data[data.symbol].timestamp:
            latest_data[data.symbol] = data
    
    # Convert to ticker format
    tickers = []
    for symbol, data in latest_data.items():
        # Calculate price change (simplified)
        price_change = 0  # TODO: Calculate actual price change
        price_change_percentage = 0  # TODO: Calculate actual percentage change
        
        ticker = TickerResponse(
            symbol=symbol,
            price=data.close_price,
            price_change=price_change,
            price_change_percentage=price_change_percentage,
            volume=data.volume,
            quote_volume=data.quote_volume,
            high_24h=data.high_price,  # Simplified
            low_24h=data.low_price,    # Simplified
            open_24h=data.open_price,  # Simplified
            close_24h=data.close_price,
            timestamp=data.timestamp
        )
        tickers.append(ticker)
    
    return tickers


@router.get("/indicators", response_model=List[IndicatorResponse])
def get_indicators(
    symbol: str,
    timeframe: str,
    indicator_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """Get technical indicators."""
    
    # Validate timeframe
    allowed_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
    if timeframe not in allowed_timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Timeframe must be one of: {allowed_timeframes}"
        )
    
    # Build query
    query = db.query(Indicator).filter(
        Indicator.symbol == symbol,
        Indicator.timeframe == timeframe,
        Indicator.indicator_name == indicator_name.upper()
    )
    
    # Apply date filters
    if start_date:
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        query = query.filter(Indicator.timestamp >= start_dt)
    
    if end_date:
        from datetime import datetime
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        query = query.filter(Indicator.timestamp <= end_dt)
    
    # Apply limit
    if limit > 1000:
        limit = 1000
    
    # Execute query
    indicators = query.order_by(Indicator.timestamp.desc()).limit(limit).all()
    
    return indicators


@router.get("/news", response_model=List[NewsResponse])
def get_news(
    symbol: Optional[str] = None,
    source: Optional[str] = None,
    sentiment_label: Optional[str] = None,
    impact_label: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get market news."""
    
    # Build query
    query = db.query(News)
    
    # Apply filters
    if symbol:
        query = query.filter(News.symbol == symbol)
    
    if source:
        query = query.filter(News.source == source)
    
    if sentiment_label:
        query = query.filter(News.sentiment_label == sentiment_label)
    
    if impact_label:
        query = query.filter(News.impact_label == impact_label)
    
    if start_date:
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        query = query.filter(News.published_at >= start_dt)
    
    if end_date:
        from datetime import datetime
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        query = query.filter(News.published_at <= end_dt)
    
    # Apply pagination
    news = query.order_by(News.published_at.desc()).offset(offset).limit(limit).all()
    
    return news


@router.get("/summary/{symbol}", response_model=MarketDataSummary)
def get_market_summary(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Get market summary for a symbol."""
    
    # Get latest market data (use 1m timeframe for most recent data)
    latest_data = db.query(MarketData).filter(
        MarketData.symbol == symbol,
        MarketData.timeframe == '1m'  # Use 1-minute data for real-time prices
    ).order_by(MarketData.timestamp.desc()).first()
    
    if not latest_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No market data found for symbol"
        )
    
    # Calculate 24h price change
    from datetime import datetime, timedelta
    time_24h_ago = datetime.utcnow() - timedelta(hours=24)
    
    price_24h_ago_data = db.query(MarketData).filter(
        MarketData.symbol == symbol,
        MarketData.timeframe == '1h',  # Use 1h for 24h comparison
        MarketData.timestamp <= time_24h_ago
    ).order_by(MarketData.timestamp.desc()).first()
    
    price_change_24h = 0
    price_change_percentage_24h = 0
    
    if price_24h_ago_data:
        old_price = float(price_24h_ago_data.close_price)
        current_price = float(latest_data.close_price)
        price_change_24h = current_price - old_price
        if old_price > 0:
            price_change_percentage_24h = (price_change_24h / old_price) * 100
    
    # Get 24h high/low from hourly data
    data_24h = db.query(MarketData).filter(
        MarketData.symbol == symbol,
        MarketData.timeframe == '1h',
        MarketData.timestamp >= time_24h_ago
    ).all()
    
    high_24h = latest_data.high_price
    low_24h = latest_data.low_price
    open_24h = latest_data.open_price
    volume_24h = latest_data.volume
    
    if data_24h:
        high_24h = max([float(d.high_price) for d in data_24h])
        low_24h = min([float(d.low_price) for d in data_24h])
        open_24h = data_24h[-1].open_price if data_24h else latest_data.open_price
        volume_24h = sum([float(d.volume) for d in data_24h])
    
    return MarketDataSummary(
        symbol=symbol,
        current_price=latest_data.close_price,
        price_change_24h=price_change_24h,
        price_change_percentage_24h=price_change_percentage_24h,
        volume_24h=volume_24h,
        market_cap=None,  # TODO: Add market cap calculation
        high_24h=high_24h,
        low_24h=low_24h,
        open_24h=open_24h,
        close_24h=latest_data.close_price,
        last_updated=latest_data.timestamp
    )


@router.get("/stats", response_model=MarketDataStats)
def get_market_stats(
    db: Session = Depends(get_db)
):
    """Get market data statistics."""
    
    # Get unique symbols
    symbols = db.query(MarketData.symbol).distinct().all()
    total_symbols = len(symbols)
    
    # Get total candles
    total_candles = db.query(MarketData).count()
    
    # Get last update
    last_update = db.query(MarketData.timestamp).order_by(
        MarketData.timestamp.desc()
    ).first()
    
    # Get unique timeframes
    timeframes = db.query(MarketData.timeframe).distinct().all()
    timeframe_list = [t[0] for t in timeframes]
    
    return MarketDataStats(
        total_symbols=total_symbols,
        total_candles=total_candles,
        last_update=last_update[0] if last_update else None,
        exchanges=["binance", "kraken", "kucoin"],  # TODO: Get from actual data
        timeframes=timeframe_list
    )
