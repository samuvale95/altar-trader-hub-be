"""
Market data-related database models.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MarketData(Base):
    """Market data model for OHLCV data."""
    
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)  # BTCUSDT, ETHUSDT, etc.
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 15m, 1h, 4h, 1d
    
    # OHLCV data
    open_price = Column(Numeric(20, 8), nullable=False)
    high_price = Column(Numeric(20, 8), nullable=False)
    low_price = Column(Numeric(20, 8), nullable=False)
    close_price = Column(Numeric(20, 8), nullable=False)
    volume = Column(Numeric(20, 8), nullable=False)
    
    # Additional metrics
    quote_volume = Column(Numeric(20, 8), default=0)  # Volume in quote currency
    trades_count = Column(Integer, default=0)  # Number of trades
    taker_buy_volume = Column(Numeric(20, 8), default=0)  # Taker buy volume
    taker_buy_quote_volume = Column(Numeric(20, 8), default=0)  # Taker buy quote volume
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_market_data_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
        Index('idx_market_data_timestamp', 'timestamp'),
    )


class News(Base):
    """News model for market news and sentiment analysis."""
    
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=True)  # Can be null for general market news
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(String(1000))
    source = Column(String(100))  # Reuters, Bloomberg, etc.
    
    # Sentiment analysis
    sentiment_score = Column(Numeric(5, 4))  # -1 to 1
    sentiment_label = Column(String(20))  # positive, negative, neutral
    confidence = Column(Numeric(5, 4))  # 0 to 1
    
    # Impact assessment
    impact_score = Column(Numeric(5, 4))  # 0 to 1
    impact_label = Column(String(20))  # high, medium, low
    
    # Timestamps
    published_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional metadata
    metadata = Column(JSON)  # Additional data from sentiment analysis
    
    # Indexes
    __table_args__ = (
        Index('idx_news_symbol_published', 'symbol', 'published_at'),
        Index('idx_news_sentiment', 'sentiment_score'),
    )


class Indicator(Base):
    """Technical indicators model."""
    
    __tablename__ = "indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    indicator_name = Column(String(50), nullable=False)  # RSI, MACD, BB, etc.
    
    # Indicator values
    value = Column(Numeric(20, 8))  # Main indicator value
    values = Column(JSON)  # Multiple values for complex indicators
    
    # Signal information
    signal = Column(String(20))  # buy, sell, hold
    signal_strength = Column(Numeric(5, 4))  # 0 to 1
    
    # Thresholds and levels
    overbought_level = Column(Numeric(10, 4))
    oversold_level = Column(Numeric(10, 4))
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional metadata
    metadata = Column(JSON)  # Additional indicator-specific data
    
    # Indexes
    __table_args__ = (
        Index('idx_indicators_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
        Index('idx_indicators_name', 'indicator_name'),
    )
