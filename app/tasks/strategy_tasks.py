"""
Strategy execution tasks.
"""

from celery import current_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.tasks.celery_app import celery_app
from app.models.strategy import Strategy, StrategySignal
from app.models.order import Order, OrderSide, OrderType, OrderStatus
from app.models.market_data import MarketData, Indicator
from app.services.exchange_adapters import get_exchange_adapter
from app.api.v1.websocket import send_order_update, send_portfolio_update
from datetime import datetime, timedelta
import asyncio
import uuid

logger = get_logger(__name__)


@celery_app.task(bind=True)
def execute_strategies(self):
    """Execute all active strategies."""
    
    db = SessionLocal()
    
    try:
        logger.info("Starting strategy execution")
        
        # Get all active strategies
        strategies = db.query(Strategy).filter(
            Strategy.is_active == True
        ).all()
        
        for strategy in strategies:
            try:
                # Execute strategy
                execute_strategy(strategy, db)
                
            except Exception as e:
                logger.error("Strategy execution failed", strategy_id=strategy.id, error=str(e))
                continue
        
        logger.info("Strategy execution completed")
        
    except Exception as e:
        logger.error("Strategy execution failed", error=str(e))
        raise
    finally:
        db.close()


def execute_strategy(strategy: Strategy, db: Session):
    """Execute a single strategy."""
    
    logger.info("Executing strategy", strategy_id=strategy.id, name=strategy.name)
    
    # Get latest market data for strategy symbols
    for symbol in strategy.symbols:
        try:
            # Get latest market data
            market_data = db.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.timeframe == strategy.timeframe
            ).order_by(MarketData.timestamp.desc()).first()
            
            if not market_data:
                logger.warning("No market data available", symbol=symbol)
                continue
            
            # Get technical indicators
            indicators = get_indicators(symbol, strategy.timeframe, db)
            
            # Execute strategy logic
            signal = execute_strategy_logic(strategy, market_data, indicators)
            
            if signal:
                # Create strategy signal
                strategy_signal = StrategySignal(
                    strategy_id=strategy.id,
                    symbol=symbol,
                    signal_type=signal["type"],
                    signal_strength=signal["strength"],
                    price=market_data.close_price,
                    quantity=signal.get("quantity"),
                    indicators=indicators,
                    confidence=signal.get("confidence", 0.5),
                    reasoning=signal.get("reasoning", "")
                )
                
                db.add(strategy_signal)
                db.commit()
                
                # Execute trade if not paper trading
                if not strategy.is_paper_trading:
                    execute_trade(strategy, signal, symbol, market_data.close_price, db)
                
                logger.info("Strategy signal generated", 
                          strategy_id=strategy.id, 
                          symbol=symbol, 
                          signal_type=signal["type"])
                
        except Exception as e:
            logger.error("Strategy execution failed for symbol", 
                        strategy_id=strategy.id, 
                        symbol=symbol, 
                        error=str(e))
            continue


def get_indicators(symbol: str, timeframe: str, db: Session) -> dict:
    """Get technical indicators for a symbol."""
    
    indicators = {}
    
    # Get latest indicators
    indicator_types = ["RSI", "MACD", "BB", "SMA", "EMA"]
    
    for indicator_type in indicator_types:
        indicator = db.query(Indicator).filter(
            Indicator.symbol == symbol,
            Indicator.timeframe == timeframe,
            Indicator.indicator_name == indicator_type
        ).order_by(Indicator.timestamp.desc()).first()
        
        if indicator:
            indicators[indicator_type] = {
                "value": indicator.value,
                "values": indicator.values,
                "signal": indicator.signal,
                "signal_strength": indicator.signal_strength,
                "timestamp": indicator.timestamp
            }
    
    return indicators


def execute_strategy_logic(strategy: Strategy, market_data: MarketData, indicators: dict) -> dict:
    """Execute strategy logic and generate signals."""
    
    # This is a simplified example - real strategies would be more complex
    signal = None
    
    if strategy.strategy_type == "momentum":
        signal = execute_momentum_strategy(strategy, market_data, indicators)
    elif strategy.strategy_type == "mean_reversion":
        signal = execute_mean_reversion_strategy(strategy, market_data, indicators)
    elif strategy.strategy_type == "arbitrage":
        signal = execute_arbitrage_strategy(strategy, market_data, indicators)
    else:
        # Custom strategy logic
        signal = execute_custom_strategy(strategy, market_data, indicators)
    
    return signal


def execute_momentum_strategy(strategy: Strategy, market_data: MarketData, indicators: dict) -> dict:
    """Execute momentum strategy."""
    
    # Simple momentum strategy based on RSI
    rsi = indicators.get("RSI", {}).get("value")
    
    if rsi is None:
        return None
    
    # Buy signal: RSI < 30 (oversold)
    if rsi < 30:
        return {
            "type": "buy",
            "strength": (30 - rsi) / 30,  # Higher strength for lower RSI
            "confidence": 0.8,
            "reasoning": f"RSI oversold at {rsi:.2f}",
            "quantity": calculate_position_size(strategy, market_data.close_price)
        }
    
    # Sell signal: RSI > 70 (overbought)
    elif rsi > 70:
        return {
            "type": "sell",
            "strength": (rsi - 70) / 30,  # Higher strength for higher RSI
            "confidence": 0.8,
            "reasoning": f"RSI overbought at {rsi:.2f}",
            "quantity": calculate_position_size(strategy, market_data.close_price)
        }
    
    return None


def execute_mean_reversion_strategy(strategy: Strategy, market_data: MarketData, indicators: dict) -> dict:
    """Execute mean reversion strategy."""
    
    # Simple mean reversion strategy based on Bollinger Bands
    bb = indicators.get("BB", {}).get("values")
    
    if bb is None:
        return None
    
    upper_band = bb.get("upper")
    lower_band = bb.get("lower")
    middle_band = bb.get("middle")
    
    if not all([upper_band, lower_band, middle_band]):
        return None
    
    current_price = market_data.close_price
    
    # Buy signal: Price touches lower band
    if current_price <= lower_band:
        return {
            "type": "buy",
            "strength": (lower_band - current_price) / (middle_band - lower_band),
            "confidence": 0.7,
            "reasoning": f"Price at lower Bollinger Band: {current_price:.2f} <= {lower_band:.2f}",
            "quantity": calculate_position_size(strategy, current_price)
        }
    
    # Sell signal: Price touches upper band
    elif current_price >= upper_band:
        return {
            "type": "sell",
            "strength": (current_price - upper_band) / (upper_band - middle_band),
            "confidence": 0.7,
            "reasoning": f"Price at upper Bollinger Band: {current_price:.2f} >= {upper_band:.2f}",
            "quantity": calculate_position_size(strategy, current_price)
        }
    
    return None


def execute_arbitrage_strategy(strategy: Strategy, market_data: MarketData, indicators: dict) -> dict:
    """Execute arbitrage strategy."""
    
    # TODO: Implement arbitrage logic
    # This would involve:
    # 1. Comparing prices across exchanges
    # 2. Calculating arbitrage opportunities
    # 3. Executing trades when profitable
    
    return None


def execute_custom_strategy(strategy: Strategy, market_data: MarketData, indicators: dict) -> dict:
    """Execute custom strategy based on configuration."""
    
    # TODO: Implement custom strategy logic
    # This would involve:
    # 1. Parsing strategy configuration
    # 2. Executing custom logic
    # 3. Generating signals based on custom rules
    
    return None


def calculate_position_size(strategy: Strategy, current_price: float) -> float:
    """Calculate position size based on strategy settings."""
    
    # Simple position sizing based on max position size percentage
    # In a real implementation, this would be more sophisticated
    max_position_value = 10000  # $10,000 max position value
    position_value = max_position_value * (strategy.max_position_size / 100)
    quantity = position_value / current_price
    
    return quantity


def execute_trade(strategy: Strategy, signal: dict, symbol: str, price: float, db: Session):
    """Execute a trade based on strategy signal."""
    
    try:
        # Get user's API keys
        api_keys = strategy.user.api_keys
        if not api_keys:
            logger.warning("No API keys available", user_id=strategy.user_id)
            return
        
        # Use first active API key
        api_key = next((ak for ak in api_keys if ak.is_active), None)
        if not api_key:
            logger.warning("No active API keys", user_id=strategy.user_id)
            return
        
        # Get exchange adapter
        adapter = get_exchange_adapter(api_key.exchange)
        adapter.set_credentials(
            api_key.api_key,
            api_key.secret_key,
            api_key.passphrase
        )
        
        # Determine order side
        side = OrderSide.BUY if signal["type"] == "buy" else OrderSide.SELL
        
        # Create order
        order = Order(
            user_id=strategy.user_id,
            strategy_id=strategy.id,
            client_order_id=f"order_{uuid.uuid4().hex[:16]}",
            symbol=symbol,
            side=side,
            type=OrderType.MARKET,
            quantity=signal["quantity"],
            exchange=api_key.exchange,
            status=OrderStatus.PENDING
        )
        
        db.add(order)
        db.commit()
        
        # Send order to exchange
        try:
            exchange_order = adapter.create_order(
                symbol=symbol,
                side=side.value,
                type="market",
                quantity=signal["quantity"]
            )
            
            # Update order with exchange response
            order.exchange_order_id = exchange_order.get("orderId")
            order.status = OrderStatus.FILLED
            order.filled_quantity = signal["quantity"]
            order.average_price = price
            order.filled_at = datetime.utcnow()
            
            db.commit()
            
            # Send WebSocket update
            asyncio.create_task(send_order_update(strategy.user_id, {
                "order_id": order.id,
                "status": "filled",
                "symbol": symbol,
                "side": side.value,
                "quantity": float(signal["quantity"]),
                "price": float(price),
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            logger.info("Trade executed", order_id=order.id, symbol=symbol, side=side.value)
            
        except Exception as e:
            logger.error("Failed to execute trade", order_id=order.id, error=str(e))
            order.status = OrderStatus.REJECTED
            db.commit()
            
    except Exception as e:
        logger.error("Trade execution failed", strategy_id=strategy.id, error=str(e))


@celery_app.task(bind=True)
def backtest_strategy(self, strategy_id: int, start_date: datetime, end_date: datetime):
    """Run backtest for a strategy."""
    
    db = SessionLocal()
    
    try:
        logger.info("Starting strategy backtest", strategy_id=strategy_id)
        
        # Get strategy
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            logger.error("Strategy not found", strategy_id=strategy_id)
            return
        
        # TODO: Implement backtesting logic
        # This would involve:
        # 1. Fetching historical market data
        # 2. Running strategy logic on historical data
        # 3. Calculating performance metrics
        # 4. Storing results
        
        logger.info("Strategy backtest completed", strategy_id=strategy_id)
        
    except Exception as e:
        logger.error("Strategy backtest failed", strategy_id=strategy_id, error=str(e))
        raise
    finally:
        db.close()
