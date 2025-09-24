"""
Data feeder service for collecting market data from exchanges.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.market_data import MarketData, Indicator
from app.models.portfolio import Balance, Position
from app.models.user import User
from app.services.exchange_adapters import get_exchange_adapter
from app.services.symbol_manager import symbol_manager
from app.api.v1.websocket import send_market_data_update, send_portfolio_update
from app.utils.indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_sma, calculate_ema, calculate_stochastic
)
import pandas as pd

logger = get_logger(__name__)


class DataFeeder:
    """Service for feeding market data from exchanges."""
    
    def __init__(self):
        self.exchange_adapters = {}
        # Load symbols dynamically from Binance
        self.symbols = self._load_dynamic_symbols()
        self.timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
    
    def _load_dynamic_symbols(self) -> List[str]:
        """Load symbols dynamically from Binance or use fallback."""
        try:
            # Try to get popular symbols from Binance
            symbols = symbol_manager.get_popular_symbols("USDT", 50)
            if symbols:
                logger.info(f"Loaded {len(symbols)} symbols from Binance")
                return symbols
        except Exception as e:
            logger.warning(f"Failed to load dynamic symbols: {e}")
        
        # Fallback to hardcoded list
        fallback_symbols = [
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
            "BNBUSDT", "XRPUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT"
        ]
        logger.info(f"Using fallback symbols: {len(fallback_symbols)} symbols")
        return fallback_symbols
    
    async def _get_exchange_adapter(self, exchange: str):
        """Get exchange adapter for the specified exchange."""
        
        if exchange not in self.exchange_adapters:
            try:
                adapter = get_exchange_adapter(exchange)
                if adapter:
                    self.exchange_adapters[exchange] = adapter
                    logger.info(f"Loaded {exchange} adapter")
                else:
                    logger.error(f"Failed to load {exchange} adapter")
                    return None
            except Exception as e:
                logger.error(f"Error loading {exchange} adapter: {e}")
                return None
        
        return self.exchange_adapters.get(exchange)
    
    async def get_latest_data(self, symbol: str, timeframe: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Get latest market data for a symbol and timeframe."""
        
        try:
            # Get exchange adapter
            exchange_adapter = await self._get_exchange_adapter("binance")
            if not exchange_adapter:
                logger.error("Binance adapter not available")
                return []
            
            # Get latest klines
            klines = exchange_adapter.get_klines(symbol, timeframe, limit=limit)
            
            if not klines:
                return []
            
            # Convert to our format
            market_data = []
            for kline in klines:
                data = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "open_price": float(kline['open']),
                    "high_price": float(kline['high']),
                    "low_price": float(kline['low']),
                    "close_price": float(kline['close']),
                    "volume": float(kline['volume']),
                    "quote_volume": float(kline['quote_volume']),
                    "trades_count": int(kline['trades_count']),
                    "taker_buy_volume": float(kline['taker_buy_volume']),
                    "taker_buy_quote_volume": float(kline['taker_buy_quote_volume']),
                    "timestamp": kline['timestamp']
                }
                market_data.append(data)
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting latest data for {symbol} {timeframe}: {e}")
            return []
    
    async def get_historical_data(self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get historical market data for a symbol and timeframe."""
        
        try:
            # Get exchange adapter
            exchange_adapter = await self._get_exchange_adapter("binance")
            if not exchange_adapter:
                logger.error("Binance adapter not available")
                return []
            
            # Get historical klines
            klines = exchange_adapter.get_historical_klines(
                symbol, timeframe, start_time, end_time
            )
            
            if not klines:
                return []
            
            # Convert to our format
            market_data = []
            for kline in klines:
                data = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "open_price": float(kline['open']),
                    "high_price": float(kline['high']),
                    "low_price": float(kline['low']),
                    "close_price": float(kline['close']),
                    "volume": float(kline['volume']),
                    "quote_volume": float(kline['quote_volume']),
                    "trades_count": int(kline['trades_count']),
                    "taker_buy_volume": float(kline['taker_buy_volume']),
                    "taker_buy_quote_volume": float(kline['taker_buy_quote_volume']),
                    "timestamp": kline['timestamp']
                }
                market_data.append(data)
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol} {timeframe}: {e}")
            return []

    async def collect_market_data(
        self, 
        symbols: Optional[List[str]] = None, 
        timeframes: Optional[List[str]] = None
    ) -> bool:
        """Collect market data from exchanges."""
        
        if symbols is None:
            symbols = self.symbols
        
        if timeframes is None:
            timeframes = self.timeframes
        
        db = SessionLocal()
        
        try:
            logger.info("Starting market data collection", symbols=symbols, timeframes=timeframes)
            
            # Get Binance adapter (primary data source)
            binance_adapter = get_exchange_adapter("binance")
            
            for symbol in symbols:
                for timeframe in timeframes:
                    try:
                        await self._collect_symbol_data(binance_adapter, symbol, timeframe, db)
                    except Exception as e:
                        logger.error("Failed to collect data", symbol=symbol, timeframe=timeframe, error=str(e))
                        continue
            
            db.commit()
            logger.info("Market data collection completed")
            
            return True
            
        except Exception as e:
            logger.error("Market data collection failed", error=str(e))
            db.rollback()
            return False
        finally:
            db.close()
    
    async def _collect_symbol_data(
        self, 
        adapter, 
        symbol: str, 
        timeframe: str, 
        db: Session
    ) -> None:
        """Collect data for a specific symbol and timeframe."""
        
        try:
            # Get latest data from exchange
            ohlcv_data = adapter.get_klines(symbol, timeframe, limit=100)
            
            for data in ohlcv_data:
                # Check if data already exists
                existing = db.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timeframe == timeframe,
                    MarketData.timestamp == data["timestamp"]
                ).first()
                
                if not existing:
                    # Create new market data record
                    market_data = MarketData(
                        symbol=symbol,
                        timeframe=timeframe,
                        open_price=data["open"],
                        high_price=data["high"],
                        low_price=data["low"],
                        close_price=data["close"],
                        volume=data["volume"],
                        quote_volume=data.get("quote_volume", 0),
                        trades_count=data.get("trades_count", 0),
                        taker_buy_volume=data.get("taker_buy_volume", 0),
                        taker_buy_quote_volume=data.get("taker_buy_quote_volume", 0),
                        timestamp=data["timestamp"]
                    )
                    
                    db.add(market_data)
            
            # Send real-time update
            if ohlcv_data:
                latest_data = ohlcv_data[-1]
                await send_market_data_update(symbol, {
                    "price": latest_data["close"],
                    "volume": latest_data["volume"],
                    "change": latest_data.get("change", 0),
                    "change_percent": latest_data.get("change_percent", 0),
                    "timeframe": timeframe
                })
            
        except Exception as e:
            logger.error("Failed to collect symbol data", symbol=symbol, timeframe=timeframe, error=str(e))
            raise
    
    async def sync_balances(self) -> bool:
        """Sync user balances from exchanges."""
        
        db = SessionLocal()
        
        try:
            logger.info("Starting balance sync")
            
            # Get all users with API keys
            users = db.query(User).join(User.api_keys).filter(
                User.is_active == True
            ).all()
            
            for user in users:
                try:
                    await self._sync_user_balances(user, db)
                except Exception as e:
                    logger.error("Failed to sync balances", user_id=user.id, error=str(e))
                    continue
            
            db.commit()
            logger.info("Balance sync completed")
            
            return True
            
        except Exception as e:
            logger.error("Balance sync failed", error=str(e))
            db.rollback()
            return False
        finally:
            db.close()
    
    async def _sync_user_balances(self, user: User, db: Session) -> None:
        """Sync balances for a specific user."""
        
        # Get user's API keys
        api_keys = user.api_keys
        
        for api_key in api_keys:
            if not api_key.is_active:
                continue
            
            try:
                # Get exchange adapter
                adapter = get_exchange_adapter(api_key.exchange)
                adapter.set_credentials(
                    api_key.api_key,
                    api_key.secret_key,
                    api_key.passphrase
                )
                
                # Get account balances
                balances = adapter.get_account_balances()
                
                # Update balances in database
                for balance_data in balances:
                    # Find or create balance record
                    balance = db.query(Balance).filter(
                        Balance.portfolio_id.in_(
                            db.query(Portfolio.id).filter(Portfolio.user_id == user.id)
                        ),
                        Balance.exchange == api_key.exchange,
                        Balance.asset == balance_data["asset"]
                    ).first()
                    
                    if balance:
                        balance.free = balance_data["free"]
                        balance.locked = balance_data["locked"]
                        balance.total = balance_data["total"]
                        balance.last_sync = datetime.utcnow()
                    else:
                        # Create new balance record
                        portfolio = db.query(Portfolio).filter(
                            Portfolio.user_id == user.id
                        ).first()
                        
                        if portfolio:
                            balance = Balance(
                                portfolio_id=portfolio.id,
                                exchange=api_key.exchange,
                                asset=balance_data["asset"],
                                free=balance_data["free"],
                                locked=balance_data["locked"],
                                total=balance_data["total"],
                                last_sync=datetime.utcnow()
                            )
                            db.add(balance)
                
                # Send portfolio update
                await send_portfolio_update(user.id, {
                    "type": "balance_sync",
                    "exchange": api_key.exchange,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error("Failed to sync balances for exchange", 
                           user_id=user.id, 
                           exchange=api_key.exchange, 
                           error=str(e))
                continue
    
    async def update_positions(self) -> bool:
        """Update position values based on current market prices."""
        
        db = SessionLocal()
        
        try:
            logger.info("Starting position update")
            
            # Get all active positions
            positions = db.query(Position).filter(Position.is_active == True).all()
            
            # Get Binance adapter for price updates
            binance_adapter = get_exchange_adapter("binance")
            
            for position in positions:
                try:
                    await self._update_position_price(position, binance_adapter, db)
                except Exception as e:
                    logger.error("Failed to update position", position_id=position.id, error=str(e))
                    continue
            
            db.commit()
            logger.info("Position update completed")
            
            return True
            
        except Exception as e:
            logger.error("Position update failed", error=str(e))
            db.rollback()
            return False
        finally:
            db.close()
    
    async def _update_position_price(self, position: Position, adapter, db: Session) -> None:
        """Update position price and P&L."""
        
        try:
            # Get current price
            ticker = adapter.get_ticker(position.symbol)
            current_price = ticker["price"]
            
            # Update position
            position.current_price = current_price
            position.market_value = position.quantity * current_price
            position.unrealized_pnl = position.market_value - (position.quantity * position.avg_price)
            position.unrealized_pnl_percentage = (
                position.unrealized_pnl / (position.quantity * position.avg_price) * 100
            ) if position.quantity * position.avg_price > 0 else 0
            
            # Send portfolio update
            await send_portfolio_update(position.portfolio.user_id, {
                "type": "position_update",
                "position_id": position.id,
                "symbol": position.symbol,
                "current_price": float(current_price),
                "unrealized_pnl": float(position.unrealized_pnl),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error("Failed to update position price", position_id=position.id, error=str(e))
            raise
    
    async def calculate_indicators(self, symbol: str, timeframe: str) -> bool:
        """Calculate technical indicators for a symbol."""
        
        db = SessionLocal()
        
        try:
            logger.info("Calculating indicators", symbol=symbol, timeframe=timeframe)
            
            # Get market data for the symbol
            market_data = db.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.timeframe == timeframe
            ).order_by(MarketData.timestamp.asc()).all()
            
            if len(market_data) < 50:  # Need enough data for indicators
                logger.warning("Insufficient data for indicators", symbol=symbol, count=len(market_data))
                return False
            
            # Convert to pandas DataFrame
            df = self._market_data_to_dataframe(market_data)
            
            # Calculate indicators
            await self._calculate_and_store_indicators(df, symbol, timeframe, db)
            
            db.commit()
            logger.info("Indicators calculated", symbol=symbol, timeframe=timeframe)
            
            return True
            
        except Exception as e:
            logger.error("Indicator calculation failed", symbol=symbol, timeframe=timeframe, error=str(e))
            db.rollback()
            return False
        finally:
            db.close()
    
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
    
    async def _calculate_and_store_indicators(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str, 
        db: Session
    ) -> None:
        """Calculate and store technical indicators."""
        
        # RSI
        rsi_values = calculate_rsi(df["close"], period=14)
        await self._store_indicator_values(
            db, symbol, timeframe, "RSI", rsi_values, 
            overbought_level=70, oversold_level=30
        )
        
        # MACD
        macd_values = calculate_macd(df["close"])
        await self._store_indicator_values(
            db, symbol, timeframe, "MACD", macd_values["macd"],
            values=macd_values
        )
        
        # Bollinger Bands
        bb_values = calculate_bollinger_bands(df["close"])
        await self._store_indicator_values(
            db, symbol, timeframe, "BB", bb_values["middle"],
            values=bb_values
        )
        
        # SMA
        sma_20 = calculate_sma(df["close"], period=20)
        await self._store_indicator_values(db, symbol, timeframe, "SMA_20", sma_20)
        
        sma_50 = calculate_sma(df["close"], period=50)
        await self._store_indicator_values(db, symbol, timeframe, "SMA_50", sma_50)
        
        # EMA
        ema_12 = calculate_ema(df["close"], period=12)
        await self._store_indicator_values(db, symbol, timeframe, "EMA_12", ema_12)
        
        ema_26 = calculate_ema(df["close"], period=26)
        await self._store_indicator_values(db, symbol, timeframe, "EMA_26", ema_26)
        
        # Stochastic
        stoch_values = calculate_stochastic(df["high"], df["low"], df["close"])
        await self._store_indicator_values(
            db, symbol, timeframe, "STOCH", stoch_values["k"],
            values=stoch_values, overbought_level=80, oversold_level=20
        )
    
    async def _store_indicator_values(
        self, 
        db: Session, 
        symbol: str, 
        timeframe: str, 
        indicator_name: str, 
        values: pd.Series,
        values_dict: Optional[Dict[str, Any]] = None,
        overbought_level: Optional[float] = None,
        oversold_level: Optional[float] = None
    ) -> None:
        """Store indicator values in database."""
        
        for i, (timestamp, value) in enumerate(zip(values.index, values)):
            if pd.isna(value):
                continue
            
            # Check if indicator already exists
            existing = db.query(Indicator).filter(
                Indicator.symbol == symbol,
                Indicator.timeframe == timeframe,
                Indicator.indicator_name == indicator_name,
                Indicator.timestamp == timestamp
            ).first()
            
            if existing:
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
            
            # Create indicator record
            indicator = Indicator(
                symbol=symbol,
                timeframe=timeframe,
                indicator_name=indicator_name,
                value=float(value),
                values=values_dict,
                signal=signal,
                signal_strength=abs(value - 50) / 50 if indicator_name == "RSI" else None,
                overbought_level=overbought_level,
                oversold_level=oversold_level,
                timestamp=timestamp
            )
            
            db.add(indicator)
    
    async def refresh_symbols(self) -> bool:
        """Refresh the symbols list from Binance."""
        
        try:
            logger.info("Refreshing symbols from Binance")
            
            # Refresh symbols cache
            if symbol_manager.refresh_symbols_cache():
                # Reload symbols
                self.symbols = self._load_dynamic_symbols()
                logger.info(f"Symbols refreshed: {len(self.symbols)} symbols loaded")
                return True
            else:
                logger.warning("Failed to refresh symbols cache")
                return False
                
        except Exception as e:
            logger.error(f"Failed to refresh symbols: {e}")
            return False
    
    def get_available_symbols(self, quote_asset: str = "USDT", limit: int = 100) -> List[str]:
        """Get available symbols for trading."""
        
        try:
            return symbol_manager.get_popular_symbols(quote_asset, limit)
        except Exception as e:
            logger.error(f"Failed to get available symbols: {e}")
            return self.symbols[:limit]
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol is available for trading."""
        
        try:
            return symbol_manager.validate_symbol(symbol)
        except Exception as e:
            logger.error(f"Failed to validate symbol {symbol}: {e}")
            return symbol in self.symbols
    
    async def collect_news(self) -> bool:
        """Collect market news and perform sentiment analysis."""
        
        db = SessionLocal()
        
        try:
            logger.info("Starting news collection")
            
            # TODO: Implement news collection from various sources
            # This would involve:
            # 1. Fetching news from APIs (NewsAPI, Alpha Vantage, etc.)
            # 2. Performing sentiment analysis
            # 3. Storing in database
            
            logger.info("News collection completed")
            
            return True
            
        except Exception as e:
            logger.error("News collection failed", error=str(e))
            return False
        finally:
            db.close()


# Global data feeder instance
data_feeder = DataFeeder()
