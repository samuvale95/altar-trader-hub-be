"""
Market data-related Pydantic schemas.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, validator


# Market data schemas
class MarketDataBase(BaseModel):
    """Base market data schema."""
    symbol: str
    timeframe: str
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal


class MarketDataResponse(MarketDataBase):
    """Schema for market data responses."""
    id: int
    quote_volume: Decimal
    trades_count: int
    taker_buy_volume: Decimal
    taker_buy_quote_volume: Decimal
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class MarketDataRequest(BaseModel):
    """Schema for market data requests."""
    symbol: str
    timeframe: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 1000
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        allowed_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
        if v not in allowed_timeframes:
            raise ValueError(f'Timeframe must be one of: {allowed_timeframes}')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if v > 1000:
            raise ValueError('Limit cannot exceed 1000')
        return v


# News schemas
class NewsResponse(BaseModel):
    """Schema for news responses."""
    id: int
    symbol: Optional[str] = None
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    source: str
    sentiment_score: Optional[Decimal] = None
    sentiment_label: Optional[str] = None
    confidence: Optional[Decimal] = None
    impact_score: Optional[Decimal] = None
    impact_label: Optional[str] = None
    published_at: datetime
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class NewsRequest(BaseModel):
    """Schema for news requests."""
    symbol: Optional[str] = None
    source: Optional[str] = None
    sentiment_label: Optional[str] = None
    impact_label: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


# Indicator schemas
class IndicatorResponse(BaseModel):
    """Schema for indicator responses."""
    id: int
    symbol: str
    timeframe: str
    indicator_name: str
    value: Optional[Decimal] = None
    values: Optional[Dict[str, Any]] = None
    signal: Optional[str] = None
    signal_strength: Optional[Decimal] = None
    overbought_level: Optional[Decimal] = None
    oversold_level: Optional[Decimal] = None
    timestamp: datetime
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class IndicatorRequest(BaseModel):
    """Schema for indicator requests."""
    symbol: str
    timeframe: str
    indicator_name: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 1000
    
    @validator('indicator_name')
    def validate_indicator_name(cls, v):
        allowed_indicators = [
            'RSI', 'MACD', 'BB', 'SMA', 'EMA', 'WMA', 'DMA', 'TEMA', 'TRIMA',
            'KAMA', 'MAMA', 'VWMA', 'T3', 'ADX', 'AROON', 'AROONOSC', 'BOP',
            'CCI', 'CMO', 'DX', 'MFI', 'MINUS_DI', 'MINUS_DM', 'MOM', 'PLUS_DI',
            'PLUS_DM', 'PPO', 'ROC', 'ROCP', 'ROCR', 'ROCR100', 'STOCH', 'STOCHF',
            'STOCHRSI', 'TRIX', 'ULTOSC', 'WILLR', 'AD', 'ADOSC', 'OBV', 'ATR',
            'NATR', 'TRANGE', 'HT_DCPERIOD', 'HT_DCPHASE', 'HT_PHASOR', 'HT_SINE',
            'HT_TRENDMODE', 'CDL2CROWS', 'CDL3BLACKCROWS', 'CDL3INSIDE', 'CDL3LINESTRIKE',
            'CDL3OUTSIDE', 'CDL3STARSINSOUTH', 'CDL3WHITESOLDIERS', 'CDLABANDONEDBABY',
            'CDLADVANCEBLOCK', 'CDLBELTHOLD', 'CDLBREAKAWAY', 'CDLCLOSINGMARUBOZU',
            'CDLCONCEALBABYSWALL', 'CDLCOUNTERATTACK', 'CDLDARKCLOUDCOVER', 'CDLDOJI',
            'CDLDOJISTAR', 'CDLDRAGONFLYDOJI', 'CDLENGULFING', 'CDLEVENINGDOJISTAR',
            'CDLEVENINGSTAR', 'CDLGAPSIDESIDEWHITE', 'CDLGRAVESTONEDOJI', 'CDLHAMMER',
            'CDLHANGINGMAN', 'CDLHARAMI', 'CDLHARAMICROSS', 'CDLHIGHWAVE', 'CDLHIKKAKE',
            'CDLHIKKAKEMOD', 'CDLHOMINGPIGEON', 'CDLIDENTICAL3CROWS', 'CDLINNECK',
            'CDLINVERTEDHAMMER', 'CDLKICKING', 'CDLKICKINGBYLENGTH', 'CDLLADDERBOTTOM',
            'CDLLONGLEGGEDDOJI', 'CDLLONGLINE', 'CDLMARUBOZU', 'CDLMATCHINGLOW',
            'CDLMATHOLD', 'CDLMORNINGDOJISTAR', 'CDLMORNINGSTAR', 'CDLONNECK',
            'CDLPIERCING', 'CDLRICKSHAWMAN', 'CDLRISEFALL3METHODS', 'CDLSEPARATINGLINES',
            'CDLSHOOTINGSTAR', 'CDLSHORTLINE', 'CDLSPINNINGTOP', 'CDLSTALLEDPATTERN',
            'CDLSTICKSANDWICH', 'CDLTAKURI', 'CDLTASUKIGAP', 'CDLTHRUSTING', 'CDLTRISTAR',
            'CDLUNIQUE3RIVER', 'CDLUPSIDEGAP2CROWS', 'CDLXSIDEGAP3METHODS'
        ]
        if v.upper() not in allowed_indicators:
            raise ValueError(f'Indicator name must be one of the supported indicators')
        return v.upper()


# Ticker schemas
class TickerResponse(BaseModel):
    """Schema for ticker responses."""
    symbol: str
    price: Decimal
    price_change: Decimal
    price_change_percentage: Decimal
    volume: Decimal
    quote_volume: Decimal
    high_24h: Decimal
    low_24h: Decimal
    open_24h: Decimal
    close_24h: Decimal
    timestamp: datetime


class TickerRequest(BaseModel):
    """Schema for ticker requests."""
    symbols: Optional[List[str]] = None
    exchange: Optional[str] = None


# Market data summary schemas
class MarketDataSummary(BaseModel):
    """Schema for market data summary."""
    symbol: str
    current_price: Decimal
    price_change_24h: Decimal
    price_change_percentage_24h: Decimal
    volume_24h: Decimal
    market_cap: Optional[Decimal] = None
    high_24h: Decimal
    low_24h: Decimal
    open_24h: Decimal
    close_24h: Decimal
    last_updated: datetime


class MarketDataStats(BaseModel):
    """Schema for market data statistics."""
    total_symbols: int
    total_candles: int
    last_update: datetime
    exchanges: List[str]
    timeframes: List[str]


# Chart-specific schemas
class ChartDataPoint(BaseModel):
    """Chart data point for candlestick charts."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class ChartData(BaseModel):
    """Chart data response."""
    symbol: str
    timeframe: str
    data: List[ChartDataPoint]
    count: int
    start_time: str
    end_time: str


class PriceHistoryPoint(BaseModel):
    """Price history data point."""
    timestamp: str
    price: float
    volume: float
    open: float
    high: float
    low: float
    close: float


class PriceHistory(BaseModel):
    """Price history response."""
    symbol: str
    timeframe: str
    prices: List[PriceHistoryPoint]
    count: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class VolumeDataPoint(BaseModel):
    """Volume data point."""
    timestamp: str
    volume: float
    quote_volume: float
    trades_count: int


class VolumeData(BaseModel):
    """Volume data response."""
    symbol: str
    timeframe: str
    data: List[VolumeDataPoint]
    count: int


class TechnicalIndicatorPoint(BaseModel):
    """Technical indicator data point."""
    timestamp: str
    value: Optional[float] = None
    values: Optional[Dict[str, Any]] = None
    signal: Optional[str] = None
    signal_strength: Optional[float] = None


class TechnicalIndicatorData(BaseModel):
    """Technical indicator data response."""
    symbol: str
    timeframe: str
    indicator_name: str
    data: List[TechnicalIndicatorPoint]
    count: int
    overbought_level: Optional[float] = None
    oversold_level: Optional[float] = None


class ChartRequest(BaseModel):
    """Chart data request."""
    symbol: str
    timeframe: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 1000
    indicators: Optional[List[str]] = None
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        allowed_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
        if v not in allowed_timeframes:
            raise ValueError(f'Timeframe must be one of: {allowed_timeframes}')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if v > 2000:
            raise ValueError('Limit cannot exceed 2000')
        return v


class SymbolInfo(BaseModel):
    """Symbol information."""
    symbol: str
    data_points: int
    latest_price: Optional[float] = None
    latest_timestamp: Optional[str] = None
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None


class AvailableSymbolsResponse(BaseModel):
    """Available symbols response."""
    symbols: List[SymbolInfo]
    total_symbols: int


class TimeframeInfo(BaseModel):
    """Timeframe information."""
    timeframe: str
    data_points: int
    latest_timestamp: Optional[str] = None


class AvailableTimeframesResponse(BaseModel):
    """Available timeframes response."""
    symbol: str
    timeframes: List[TimeframeInfo]
    total_timeframes: int


class ChartSummary(BaseModel):
    """Chart summary data."""
    symbol: str
    timeframe: str
    current_price: float
    price_change: float
    price_change_percentage: float
    volume_24h: float
    high_24h: float
    low_24h: float
    open_24h: float
    close_24h: float
    last_updated: str
