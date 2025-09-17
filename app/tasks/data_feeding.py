"""
Data feeding tasks for market data collection.
"""

from celery import current_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.tasks.celery_app import celery_app
from app.models.market_data import MarketData
from app.models.portfolio import Balance, Position
from app.models.user import User
from app.services.exchange_adapters import get_exchange_adapter
from app.api.v1.websocket import send_market_data_update, send_portfolio_update
from datetime import datetime, timedelta
import asyncio

logger = get_logger(__name__)


@celery_app.task(bind=True)
def collect_market_data(self, symbols=None, timeframes=None):
    """Collect market data from exchanges."""
    
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
    
    if timeframes is None:
        timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
    
    db = SessionLocal()
    
    try:
        logger.info("Starting market data collection", symbols=symbols, timeframes=timeframes)
        
        # Get Binance adapter
        binance_adapter = get_exchange_adapter("binance")
        
        for symbol in symbols:
            for timeframe in timeframes:
                try:
                    # Get latest data from exchange
                    ohlcv_data = binance_adapter.get_klines(symbol, timeframe, limit=100)
                    
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
                    latest_data = ohlcv_data[-1] if ohlcv_data else None
                    if latest_data:
                        asyncio.create_task(send_market_data_update(symbol, {
                            "price": latest_data["close"],
                            "volume": latest_data["volume"],
                            "change": latest_data.get("change", 0),
                            "change_percent": latest_data.get("change_percent", 0)
                        }))
                    
                except Exception as e:
                    logger.error("Failed to collect data", symbol=symbol, timeframe=timeframe, error=str(e))
                    continue
        
        db.commit()
        logger.info("Market data collection completed")
        
    except Exception as e:
        logger.error("Market data collection failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def sync_balances(self):
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
                # Get user's API keys
                api_keys = user.api_keys
                
                for api_key in api_keys:
                    if not api_key.is_active:
                        continue
                    
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
                    asyncio.create_task(send_portfolio_update(user.id, {
                        "type": "balance_sync",
                        "exchange": api_key.exchange,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    
            except Exception as e:
                logger.error("Failed to sync balances", user_id=user.id, error=str(e))
                continue
        
        db.commit()
        logger.info("Balance sync completed")
        
    except Exception as e:
        logger.error("Balance sync failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def update_positions(self):
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
                # Get current price
                ticker = binance_adapter.get_ticker(position.symbol)
                current_price = ticker["price"]
                
                # Update position
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                position.unrealized_pnl = position.market_value - (position.quantity * position.avg_price)
                position.unrealized_pnl_percentage = (
                    position.unrealized_pnl / (position.quantity * position.avg_price) * 100
                ) if position.quantity * position.avg_price > 0 else 0
                
                # Send portfolio update
                asyncio.create_task(send_portfolio_update(position.portfolio.user_id, {
                    "type": "position_update",
                    "position_id": position.id,
                    "symbol": position.symbol,
                    "current_price": float(current_price),
                    "unrealized_pnl": float(position.unrealized_pnl),
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            except Exception as e:
                logger.error("Failed to update position", position_id=position.id, error=str(e))
                continue
        
        db.commit()
        logger.info("Position update completed")
        
    except Exception as e:
        logger.error("Position update failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def collect_news(self):
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
        
    except Exception as e:
        logger.error("News collection failed", error=str(e))
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def calculate_indicators(self, symbol, timeframe):
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
            return
        
        # Convert to pandas DataFrame
        import pandas as pd
        df = pd.DataFrame([{
            "timestamp": data.timestamp,
            "open": float(data.open_price),
            "high": float(data.high_price),
            "low": float(data.low_price),
            "close": float(data.close_price),
            "volume": float(data.volume)
        } for data in market_data])
        
        # Calculate indicators
        from app.utils.indicators import calculate_rsi, calculate_macd, calculate_bollinger_bands
        
        # RSI
        rsi_values = calculate_rsi(df["close"], period=14)
        
        # MACD
        macd_values = calculate_macd(df["close"])
        
        # Bollinger Bands
        bb_values = calculate_bollinger_bands(df["close"], period=20)
        
        # Store indicators
        for i, (timestamp, rsi, macd, bb) in enumerate(zip(
            df["timestamp"], rsi_values, macd_values, bb_values
        )):
            # RSI
            if not pd.isna(rsi):
                indicator = Indicator(
                    symbol=symbol,
                    timeframe=timeframe,
                    indicator_name="RSI",
                    value=rsi,
                    overbought_level=70,
                    oversold_level=30,
                    timestamp=timestamp
                )
                db.add(indicator)
            
            # MACD
            if not pd.isna(macd["macd"]):
                indicator = Indicator(
                    symbol=symbol,
                    timeframe=timeframe,
                    indicator_name="MACD",
                    values={
                        "macd": macd["macd"],
                        "signal": macd["signal"],
                        "histogram": macd["histogram"]
                    },
                    timestamp=timestamp
                )
                db.add(indicator)
            
            # Bollinger Bands
            if not pd.isna(bb["upper"]):
                indicator = Indicator(
                    symbol=symbol,
                    timeframe=timeframe,
                    indicator_name="BB",
                    values={
                        "upper": bb["upper"],
                        "middle": bb["middle"],
                        "lower": bb["lower"]
                    },
                    timestamp=timestamp
                )
                db.add(indicator)
        
        db.commit()
        logger.info("Indicators calculated", symbol=symbol, timeframe=timeframe)
        
    except Exception as e:
        logger.error("Indicator calculation failed", symbol=symbol, timeframe=timeframe, error=str(e))
        db.rollback()
        raise
    finally:
        db.close()
