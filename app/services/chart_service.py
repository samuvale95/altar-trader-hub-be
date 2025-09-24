"""
Chart service for processing market data and generating chart-ready data.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.models.market_data import MarketData, Indicator
from app.schemas.market_data import (
    ChartData, ChartDataPoint, PriceHistory, PriceHistoryPoint,
    VolumeData, VolumeDataPoint, TechnicalIndicatorData, TechnicalIndicatorPoint,
    ChartSummary, SymbolInfo, TimeframeInfo
)
from app.utils.indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_sma, calculate_ema, calculate_stochastic, calculate_atr
)
import pandas as pd

logger = get_logger(__name__)


class ChartService:
    """Service for processing chart data and technical indicators."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_candlestick_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 1000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ChartData:
        """Get candlestick data for a symbol."""
        
        try:
            # Build query
            query = self.db.query(MarketData).filter(
                MarketData.symbol == symbol.upper(),
                MarketData.timeframe == timeframe
            )
            
            # Apply date filters
            if start_date:
                query = query.filter(MarketData.timestamp >= start_date)
            if end_date:
                query = query.filter(MarketData.timestamp <= end_date)
            
            # Get data
            market_data = query.order_by(MarketData.timestamp.desc()).limit(limit).all()
            
            if not market_data:
                raise ValueError(f"No data found for {symbol} {timeframe}")
            
            # Convert to chart format
            candles = []
            for data in reversed(market_data):  # Reverse to get chronological order
                candles.append(ChartDataPoint(
                    timestamp=data.timestamp.isoformat(),
                    open=float(data.open_price),
                    high=float(data.high_price),
                    low=float(data.low_price),
                    close=float(data.close_price),
                    volume=float(data.volume)
                ))
            
            return ChartData(
                symbol=symbol.upper(),
                timeframe=timeframe,
                data=candles,
                count=len(candles),
                start_time=candles[0].timestamp if candles else None,
                end_time=candles[-1].timestamp if candles else None
            )
            
        except Exception as e:
            logger.error(f"Error getting candlestick data for {symbol}: {e}")
            raise
    
    def get_price_history(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 1000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PriceHistory:
        """Get price history for a symbol."""
        
        try:
            # Build query
            query = self.db.query(MarketData).filter(
                MarketData.symbol == symbol.upper(),
                MarketData.timeframe == timeframe
            )
            
            # Apply date filters
            if start_date:
                query = query.filter(MarketData.timestamp >= start_date)
            if end_date:
                query = query.filter(MarketData.timestamp <= end_date)
            
            # Get data
            market_data = query.order_by(MarketData.timestamp.desc()).limit(limit).all()
            
            if not market_data:
                raise ValueError(f"No data found for {symbol} {timeframe}")
            
            # Convert to price history format
            prices = []
            for data in reversed(market_data):  # Reverse to get chronological order
                prices.append(PriceHistoryPoint(
                    timestamp=data.timestamp.isoformat(),
                    price=float(data.close_price),
                    volume=float(data.volume),
                    open=float(data.open_price),
                    high=float(data.high_price),
                    low=float(data.low_price),
                    close=float(data.close_price)
                ))
            
            return PriceHistory(
                symbol=symbol.upper(),
                timeframe=timeframe,
                prices=prices,
                count=len(prices),
                start_time=prices[0].timestamp if prices else None,
                end_time=prices[-1].timestamp if prices else None
            )
            
        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {e}")
            raise
    
    def get_volume_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 1000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> VolumeData:
        """Get volume data for a symbol."""
        
        try:
            # Build query
            query = self.db.query(MarketData).filter(
                MarketData.symbol == symbol.upper(),
                MarketData.timeframe == timeframe
            )
            
            # Apply date filters
            if start_date:
                query = query.filter(MarketData.timestamp >= start_date)
            if end_date:
                query = query.filter(MarketData.timestamp <= end_date)
            
            # Get data
            market_data = query.order_by(MarketData.timestamp.desc()).limit(limit).all()
            
            if not market_data:
                raise ValueError(f"No data found for {symbol} {timeframe}")
            
            # Convert to volume format
            volume_data = []
            for data in reversed(market_data):  # Reverse to get chronological order
                volume_data.append(VolumeDataPoint(
                    timestamp=data.timestamp.isoformat(),
                    volume=float(data.volume),
                    quote_volume=float(data.quote_volume),
                    trades_count=int(data.trades_count)
                ))
            
            return VolumeData(
                symbol=symbol.upper(),
                timeframe=timeframe,
                data=volume_data,
                count=len(volume_data)
            )
            
        except Exception as e:
            logger.error(f"Error getting volume data for {symbol}: {e}")
            raise
    
    def get_technical_indicator(
        self,
        symbol: str,
        timeframe: str,
        indicator_name: str,
        limit: int = 1000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TechnicalIndicatorData:
        """Get technical indicator data for a symbol."""
        
        try:
            # Build query
            query = self.db.query(Indicator).filter(
                Indicator.symbol == symbol.upper(),
                Indicator.timeframe == timeframe,
                Indicator.indicator_name == indicator_name.upper()
            )
            
            # Apply date filters
            if start_date:
                query = query.filter(Indicator.timestamp >= start_date)
            if end_date:
                query = query.filter(Indicator.timestamp <= end_date)
            
            # Get data
            indicators = query.order_by(Indicator.timestamp.desc()).limit(limit).all()
            
            if not indicators:
                raise ValueError(f"No indicator data found for {symbol} {timeframe} {indicator_name}")
            
            # Convert to indicator format
            indicator_data = []
            for indicator in reversed(indicators):  # Reverse to get chronological order
                indicator_data.append(TechnicalIndicatorPoint(
                    timestamp=indicator.timestamp.isoformat(),
                    value=float(indicator.value) if indicator.value else None,
                    values=indicator.values,
                    signal=indicator.signal,
                    signal_strength=float(indicator.signal_strength) if indicator.signal_strength else None
                ))
            
            return TechnicalIndicatorData(
                symbol=symbol.upper(),
                timeframe=timeframe,
                indicator_name=indicator_name.upper(),
                data=indicator_data,
                count=len(indicator_data),
                overbought_level=float(indicators[0].overbought_level) if indicators[0].overbought_level else None,
                oversold_level=float(indicators[0].oversold_level) if indicators[0].oversold_level else None
            )
            
        except Exception as e:
            logger.error(f"Error getting technical indicator for {symbol}: {e}")
            raise
    
    def calculate_technical_indicators(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 1000
    ) -> Dict[str, TechnicalIndicatorData]:
        """Calculate and return technical indicators for a symbol."""
        
        try:
            # Get market data
            market_data = self.db.query(MarketData).filter(
                MarketData.symbol == symbol.upper(),
                MarketData.timeframe == timeframe
            ).order_by(MarketData.timestamp.asc()).limit(limit).all()
            
            if len(market_data) < 50:  # Need enough data for indicators
                raise ValueError(f"Insufficient data for indicators: {len(market_data)} points")
            
            # Convert to pandas DataFrame
            df = self._market_data_to_dataframe(market_data)
            
            # Calculate indicators
            indicators = {}
            
            # RSI
            rsi_values = calculate_rsi(df["close"], period=14)
            indicators["RSI"] = self._create_indicator_data(
                symbol, timeframe, "RSI", rsi_values, 
                overbought_level=70, oversold_level=30
            )
            
            # MACD
            macd_values = calculate_macd(df["close"])
            indicators["MACD"] = self._create_indicator_data(
                symbol, timeframe, "MACD", macd_values["macd"],
                values=macd_values
            )
            
            # Bollinger Bands
            bb_values = calculate_bollinger_bands(df["close"])
            indicators["BB"] = self._create_indicator_data(
                symbol, timeframe, "BB", bb_values["middle"],
                values=bb_values
            )
            
            # SMA
            sma_20 = calculate_sma(df["close"], period=20)
            indicators["SMA_20"] = self._create_indicator_data(symbol, timeframe, "SMA_20", sma_20)
            
            sma_50 = calculate_sma(df["close"], period=50)
            indicators["SMA_50"] = self._create_indicator_data(symbol, timeframe, "SMA_50", sma_50)
            
            # EMA
            ema_12 = calculate_ema(df["close"], period=12)
            indicators["EMA_12"] = self._create_indicator_data(symbol, timeframe, "EMA_12", ema_12)
            
            ema_26 = calculate_ema(df["close"], period=26)
            indicators["EMA_26"] = self._create_indicator_data(symbol, timeframe, "EMA_26", ema_26)
            
            # Stochastic
            stoch_values = calculate_stochastic(df["high"], df["low"], df["close"])
            indicators["STOCH"] = self._create_indicator_data(
                symbol, timeframe, "STOCH", stoch_values["k"],
                values=stoch_values, overbought_level=80, oversold_level=20
            )
            
            # ATR
            atr_values = calculate_atr(df["high"], df["low"], df["close"])
            indicators["ATR"] = self._create_indicator_data(symbol, timeframe, "ATR", atr_values)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            raise
    
    def get_chart_summary(
        self,
        symbol: str,
        timeframe: str
    ) -> ChartSummary:
        """Get chart summary data for a symbol."""
        
        try:
            # Get latest data
            latest_data = self.db.query(MarketData).filter(
                MarketData.symbol == symbol.upper(),
                MarketData.timeframe == timeframe
            ).order_by(MarketData.timestamp.desc()).first()
            
            if not latest_data:
                raise ValueError(f"No data found for {symbol} {timeframe}")
            
            # Get 24h data for comparison
            yesterday = latest_data.timestamp - timedelta(days=1)
            yesterday_data = self.db.query(MarketData).filter(
                MarketData.symbol == symbol.upper(),
                MarketData.timeframe == timeframe,
                MarketData.timestamp >= yesterday
            ).order_by(MarketData.timestamp.asc()).first()
            
            # Calculate price change
            price_change = 0
            price_change_percentage = 0
            if yesterday_data:
                price_change = float(latest_data.close_price - yesterday_data.close_price)
                price_change_percentage = (price_change / float(yesterday_data.close_price)) * 100
            
            # Get 24h high/low
            high_24h = self.db.query(MarketData.high_price).filter(
                MarketData.symbol == symbol.upper(),
                MarketData.timeframe == timeframe,
                MarketData.timestamp >= yesterday
            ).order_by(MarketData.high_price.desc()).first()
            
            low_24h = self.db.query(MarketData.low_price).filter(
                MarketData.symbol == symbol.upper(),
                MarketData.timeframe == timeframe,
                MarketData.timestamp >= yesterday
            ).order_by(MarketData.low_price.asc()).first()
            
            # Get 24h volume
            volume_24h = self.db.query(MarketData.volume).filter(
                MarketData.symbol == symbol.upper(),
                MarketData.timeframe == timeframe,
                MarketData.timestamp >= yesterday
            ).all()
            
            total_volume = sum(float(v[0]) for v in volume_24h)
            
            return ChartSummary(
                symbol=symbol.upper(),
                timeframe=timeframe,
                current_price=float(latest_data.close_price),
                price_change=price_change,
                price_change_percentage=price_change_percentage,
                volume_24h=total_volume,
                high_24h=float(high_24h[0]) if high_24h else float(latest_data.high_price),
                low_24h=float(low_24h[0]) if low_24h else float(latest_data.low_price),
                open_24h=float(yesterday_data.close_price) if yesterday_data else float(latest_data.open_price),
                close_24h=float(latest_data.close_price),
                last_updated=latest_data.timestamp.isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error getting chart summary for {symbol}: {e}")
            raise
    
    def get_available_symbols(self) -> List[SymbolInfo]:
        """Get list of available symbols with data."""
        
        try:
            # Get unique symbols with data
            symbols = self.db.query(MarketData.symbol).distinct().all()
            symbol_list = [symbol[0] for symbol in symbols]
            
            # Get data counts and latest info for each symbol
            symbol_info = []
            for symbol in symbol_list:
                count = self.db.query(MarketData).filter(MarketData.symbol == symbol).count()
                latest = self.db.query(MarketData).filter(
                    MarketData.symbol == symbol
                ).order_by(MarketData.timestamp.desc()).first()
                
                # Calculate 24h change
                price_change_24h = None
                price_change_percentage_24h = None
                if latest:
                    yesterday = latest.timestamp - timedelta(days=1)
                    yesterday_data = self.db.query(MarketData).filter(
                        MarketData.symbol == symbol,
                        MarketData.timestamp >= yesterday
                    ).order_by(MarketData.timestamp.asc()).first()
                    
                    if yesterday_data:
                        price_change_24h = float(latest.close_price - yesterday_data.close_price)
                        price_change_percentage_24h = (price_change_24h / float(yesterday_data.close_price)) * 100
                
                symbol_info.append(SymbolInfo(
                    symbol=symbol,
                    data_points=count,
                    latest_price=float(latest.close_price) if latest else None,
                    latest_timestamp=latest.timestamp.isoformat() if latest else None,
                    price_change_24h=price_change_24h,
                    price_change_percentage_24h=price_change_percentage_24h
                ))
            
            return symbol_info
            
        except Exception as e:
            logger.error(f"Error getting available symbols: {e}")
            raise
    
    def get_available_timeframes(self, symbol: str) -> List[TimeframeInfo]:
        """Get available timeframes for a symbol."""
        
        try:
            # Get unique timeframes for symbol
            timeframes = self.db.query(MarketData.timeframe).filter(
                MarketData.symbol == symbol.upper()
            ).distinct().all()
            
            timeframe_list = [tf[0] for tf in timeframes]
            
            # Get data counts for each timeframe
            timeframe_info = []
            for timeframe in timeframe_list:
                count = self.db.query(MarketData).filter(
                    MarketData.symbol == symbol.upper(),
                    MarketData.timeframe == timeframe
                ).count()
                
                latest = self.db.query(MarketData).filter(
                    MarketData.symbol == symbol.upper(),
                    MarketData.timeframe == timeframe
                ).order_by(MarketData.timestamp.desc()).first()
                
                timeframe_info.append(TimeframeInfo(
                    timeframe=timeframe,
                    data_points=count,
                    latest_timestamp=latest.timestamp.isoformat() if latest else None
                ))
            
            return timeframe_info
            
        except Exception as e:
            logger.error(f"Error getting timeframes for {symbol}: {e}")
            raise
    
    def _market_data_to_dataframe(self, market_data: List[MarketData]) -> pd.DataFrame:
        """Convert market data to pandas DataFrame."""
        
        data = []
        for md in market_data:
            data.append({
                "timestamp": md.timestamp,
                "open": float(md.open_price),
                "high": float(md.high_price),
                "low": float(md.low_price),
                "close": float(md.close_price),
                "volume": float(md.volume)
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        return df
    
    def _create_indicator_data(
        self,
        symbol: str,
        timeframe: str,
        indicator_name: str,
        values: pd.Series,
        values_dict: Optional[Dict[str, Any]] = None,
        overbought_level: Optional[float] = None,
        oversold_level: Optional[float] = None
    ) -> TechnicalIndicatorData:
        """Create technical indicator data from pandas Series."""
        
        indicator_data = []
        for i, (timestamp, value) in enumerate(zip(values.index, values)):
            if pd.isna(value):
                continue
            
            # Determine signal
            signal = None
            if overbought_level and oversold_level:
                if value >= overbought_level:
                    signal = "sell"
                elif value <= oversold_level:
                    signal = "buy"
                else:
                    signal = "hold"
            
            indicator_data.append(TechnicalIndicatorPoint(
                timestamp=timestamp.isoformat(),
                value=float(value),
                values=values_dict,
                signal=signal,
                signal_strength=abs(value - 50) / 50 if indicator_name == "RSI" else None
            ))
        
        return TechnicalIndicatorData(
            symbol=symbol.upper(),
            timeframe=timeframe,
            indicator_name=indicator_name,
            data=indicator_data,
            count=len(indicator_data),
            overbought_level=overbought_level,
            oversold_level=oversold_level
        )
