"""
Strategy engine for executing trading strategies.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.strategy import Strategy, StrategySignal, StrategyPerformance
from app.models.market_data import MarketData, Indicator
from app.models.portfolio import Position
from app.models.order import Order, OrderSide, OrderType, OrderStatus
from app.services.exchange_adapters import get_exchange_adapter
from app.services.notification_service import notification_service
from app.utils.indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_sma, calculate_ema, calculate_stochastic
)
import pandas as pd
import numpy as np

logger = get_logger(__name__)


class StrategyEngine:
    """Engine for executing trading strategies."""
    
    def __init__(self):
        self.active_strategies = {}
        self.strategy_instances = {}
    
    async def execute_strategy(self, strategy_id: int) -> bool:
        """Execute a single strategy."""
        
        db = SessionLocal()
        
        try:
            # Get strategy
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy or not strategy.is_active:
                logger.warning("Strategy not found or inactive", strategy_id=strategy_id)
                return False
            
            logger.info("Executing strategy", strategy_id=strategy_id, name=strategy.name)
            
            # Execute strategy for each symbol
            for symbol in strategy.symbols:
                try:
                    await self._execute_strategy_for_symbol(strategy, symbol, db)
                except Exception as e:
                    logger.error("Failed to execute strategy for symbol", 
                               strategy_id=strategy_id, 
                               symbol=symbol, 
                               error=str(e))
                    continue
            
            # Update strategy last execution time
            strategy.last_execution = datetime.utcnow()
            db.commit()
            
            logger.info("Strategy execution completed", strategy_id=strategy_id)
            return True
            
        except Exception as e:
            logger.error("Strategy execution failed", strategy_id=strategy_id, error=str(e))
            db.rollback()
            return False
        finally:
            db.close()
    
    async def _execute_strategy_for_symbol(
        self, 
        strategy: Strategy, 
        symbol: str, 
        db: Session
    ) -> None:
        """Execute strategy for a specific symbol."""
        
        # Get latest market data
        market_data = db.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.timeframe == strategy.timeframe
        ).order_by(MarketData.timestamp.desc()).limit(100).all()
        
        if len(market_data) < 50:  # Need enough data for indicators
            logger.warning("Insufficient market data", symbol=symbol, count=len(market_data))
            return
        
        # Convert to DataFrame
        df = self._market_data_to_dataframe(market_data)
        
        # Get technical indicators
        indicators = await self._calculate_indicators(df, symbol, strategy.timeframe, db)
        
        # Execute strategy logic
        signal = await self._execute_strategy_logic(strategy, df, indicators, symbol)
        
        if signal:
            # Create strategy signal
            strategy_signal = StrategySignal(
                strategy_id=strategy.id,
                symbol=symbol,
                signal_type=signal["type"],
                signal_strength=signal["strength"],
                price=float(df.iloc[-1]["close"]),
                quantity=signal.get("quantity"),
                indicators=indicators,
                confidence=signal.get("confidence", 0.5),
                reasoning=signal.get("reasoning", "")
            )
            
            db.add(strategy_signal)
            db.commit()
            
            # Execute trade if not paper trading
            if not strategy.is_paper_trading:
                await self._execute_trade(strategy, signal, symbol, float(df.iloc[-1]["close"]), db)
            
            # Send notification
            await notification_service.send_strategy_signal_notification(
                user_id=strategy.user_id,
                signal_data={
                    "strategy_name": strategy.name,
                    "symbol": symbol,
                    "signal_type": signal["type"],
                    "price": float(df.iloc[-1]["close"]),
                    "confidence": signal.get("confidence", 0.5),
                    "reasoning": signal.get("reasoning", "")
                }
            )
            
            logger.info("Strategy signal generated", 
                       strategy_id=strategy.id, 
                       symbol=symbol, 
                       signal_type=signal["type"])
    
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
    
    async def _calculate_indicators(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str, 
        db: Session
    ) -> Dict[str, Any]:
        """Calculate technical indicators."""
        
        indicators = {}
        
        # RSI
        rsi = calculate_rsi(df["close"], period=14)
        if not rsi.empty and not pd.isna(rsi.iloc[-1]):
            indicators["RSI"] = {
                "value": float(rsi.iloc[-1]),
                "signal": "oversold" if rsi.iloc[-1] < 30 else "overbought" if rsi.iloc[-1] > 70 else "neutral",
                "signal_strength": abs(rsi.iloc[-1] - 50) / 50
            }
        
        # MACD
        macd = calculate_macd(df["close"])
        if not macd["macd"].empty and not pd.isna(macd["macd"].iloc[-1]):
            indicators["MACD"] = {
                "macd": float(macd["macd"].iloc[-1]),
                "signal": float(macd["signal"].iloc[-1]),
                "histogram": float(macd["histogram"].iloc[-1]),
                "signal_type": "buy" if macd["histogram"].iloc[-1] > 0 else "sell"
            }
        
        # Bollinger Bands
        bb = calculate_bollinger_bands(df["close"])
        if not bb["upper"].empty and not pd.isna(bb["upper"].iloc[-1]):
            current_price = df["close"].iloc[-1]
            upper_band = bb["upper"].iloc[-1]
            lower_band = bb["lower"].iloc[-1]
            middle_band = bb["middle"].iloc[-1]
            
            indicators["BB"] = {
                "upper": float(upper_band),
                "middle": float(middle_band),
                "lower": float(lower_band),
                "signal": "sell" if current_price >= upper_band else "buy" if current_price <= lower_band else "neutral",
                "position": (current_price - lower_band) / (upper_band - lower_band)
            }
        
        # SMA
        sma_20 = calculate_sma(df["close"], period=20)
        sma_50 = calculate_sma(df["close"], period=50)
        
        if not sma_20.empty and not pd.isna(sma_20.iloc[-1]):
            indicators["SMA_20"] = float(sma_20.iloc[-1])
        
        if not sma_50.empty and not pd.isna(sma_50.iloc[-1]):
            indicators["SMA_50"] = float(sma_50.iloc[-1])
        
        # EMA
        ema_12 = calculate_ema(df["close"], period=12)
        ema_26 = calculate_ema(df["close"], period=26)
        
        if not ema_12.empty and not pd.isna(ema_12.iloc[-1]):
            indicators["EMA_12"] = float(ema_12.iloc[-1])
        
        if not ema_26.empty and not pd.isna(ema_26.iloc[-1]):
            indicators["EMA_26"] = float(ema_26.iloc[-1])
        
        # Stochastic
        stoch = calculate_stochastic(df["high"], df["low"], df["close"])
        if not stoch["k"].empty and not pd.isna(stoch["k"].iloc[-1]):
            indicators["STOCH"] = {
                "k": float(stoch["k"].iloc[-1]),
                "d": float(stoch["d"].iloc[-1]),
                "signal": "oversold" if stoch["k"].iloc[-1] < 20 else "overbought" if stoch["k"].iloc[-1] > 80 else "neutral"
            }
        
        return indicators
    
    async def _execute_strategy_logic(
        self, 
        strategy: Strategy, 
        df: pd.DataFrame, 
        indicators: Dict[str, Any], 
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """Execute strategy logic and generate signals."""
        
        # Get strategy configuration
        config = strategy.config or {}
        
        # Execute based on strategy type
        if strategy.strategy_type == "momentum":
            return await self._execute_momentum_strategy(strategy, df, indicators, config)
        elif strategy.strategy_type == "mean_reversion":
            return await self._execute_mean_reversion_strategy(strategy, df, indicators, config)
        elif strategy.strategy_type == "arbitrage":
            return await self._execute_arbitrage_strategy(strategy, df, indicators, config)
        elif strategy.strategy_type == "scalping":
            return await self._execute_scalping_strategy(strategy, df, indicators, config)
        elif strategy.strategy_type == "swing":
            return await self._execute_swing_strategy(strategy, df, indicators, config)
        else:
            return await self._execute_custom_strategy(strategy, df, indicators, config)
    
    async def _execute_momentum_strategy(
        self, 
        strategy: Strategy, 
        df: pd.DataFrame, 
        indicators: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute momentum strategy."""
        
        # Get RSI
        rsi = indicators.get("RSI", {})
        if not rsi:
            return None
        
        rsi_value = rsi.get("value", 50)
        rsi_signal = rsi.get("signal", "neutral")
        
        # Get MACD
        macd = indicators.get("MACD", {})
        macd_signal = macd.get("signal_type", "neutral")
        
        # Get price momentum
        price_change = (df["close"].iloc[-1] - df["close"].iloc[-5]) / df["close"].iloc[-5] * 100
        
        # Buy signal: RSI oversold + MACD bullish + positive momentum
        if (rsi_signal == "oversold" and 
            macd_signal == "buy" and 
            price_change > 0):
            
            return {
                "type": "buy",
                "strength": min(1.0, (30 - rsi_value) / 30 + abs(price_change) / 10),
                "confidence": 0.8,
                "reasoning": f"RSI oversold ({rsi_value:.2f}), MACD bullish, positive momentum ({price_change:.2f}%)",
                "quantity": self._calculate_position_size(strategy, df["close"].iloc[-1])
            }
        
        # Sell signal: RSI overbought + MACD bearish + negative momentum
        elif (rsi_signal == "overbought" and 
              macd_signal == "sell" and 
              price_change < 0):
            
            return {
                "type": "sell",
                "strength": min(1.0, (rsi_value - 70) / 30 + abs(price_change) / 10),
                "confidence": 0.8,
                "reasoning": f"RSI overbought ({rsi_value:.2f}), MACD bearish, negative momentum ({price_change:.2f}%)",
                "quantity": self._calculate_position_size(strategy, df["close"].iloc[-1])
            }
        
        return None
    
    async def _execute_mean_reversion_strategy(
        self, 
        strategy: Strategy, 
        df: pd.DataFrame, 
        indicators: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute mean reversion strategy."""
        
        # Get Bollinger Bands
        bb = indicators.get("BB", {})
        if not bb:
            return None
        
        current_price = df["close"].iloc[-1]
        upper_band = bb.get("upper", current_price)
        lower_band = bb.get("lower", current_price)
        middle_band = bb.get("middle", current_price)
        position = bb.get("position", 0.5)
        
        # Get RSI for confirmation
        rsi = indicators.get("RSI", {})
        rsi_value = rsi.get("value", 50)
        
        # Buy signal: Price at lower band + RSI oversold
        if current_price <= lower_band and rsi_value < 30:
            return {
                "type": "buy",
                "strength": min(1.0, (lower_band - current_price) / (middle_band - lower_band) + (30 - rsi_value) / 30),
                "confidence": 0.7,
                "reasoning": f"Price at lower Bollinger Band ({current_price:.2f} <= {lower_band:.2f}), RSI oversold ({rsi_value:.2f})",
                "quantity": self._calculate_position_size(strategy, current_price)
            }
        
        # Sell signal: Price at upper band + RSI overbought
        elif current_price >= upper_band and rsi_value > 70:
            return {
                "type": "sell",
                "strength": min(1.0, (current_price - upper_band) / (upper_band - middle_band) + (rsi_value - 70) / 30),
                "confidence": 0.7,
                "reasoning": f"Price at upper Bollinger Band ({current_price:.2f} >= {upper_band:.2f}), RSI overbought ({rsi_value:.2f})",
                "quantity": self._calculate_position_size(strategy, current_price)
            }
        
        return None
    
    async def _execute_arbitrage_strategy(
        self, 
        strategy: Strategy, 
        df: pd.DataFrame, 
        indicators: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute arbitrage strategy."""
        
        # TODO: Implement arbitrage strategy
        # This would involve:
        # 1. Comparing prices across exchanges
        # 2. Calculating arbitrage opportunities
        # 3. Executing trades when profitable
        
        return None
    
    async def _execute_scalping_strategy(
        self, 
        strategy: Strategy, 
        df: pd.DataFrame, 
        indicators: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute scalping strategy."""
        
        # Get short-term indicators
        rsi = indicators.get("RSI", {})
        stoch = indicators.get("STOCH", {})
        
        if not rsi or not stoch:
            return None
        
        rsi_value = rsi.get("value", 50)
        stoch_k = stoch.get("k", 50)
        stoch_d = stoch.get("d", 50)
        
        # Scalping buy: RSI and Stochastic both oversold
        if rsi_value < 35 and stoch_k < 25 and stoch_d < 25:
            return {
                "type": "buy",
                "strength": min(1.0, (35 - rsi_value) / 35 + (25 - stoch_k) / 25),
                "confidence": 0.6,
                "reasoning": f"Scalping buy: RSI ({rsi_value:.2f}) and Stochastic ({stoch_k:.2f}) oversold",
                "quantity": self._calculate_position_size(strategy, df["close"].iloc[-1])
            }
        
        # Scalping sell: RSI and Stochastic both overbought
        elif rsi_value > 65 and stoch_k > 75 and stoch_d > 75:
            return {
                "type": "sell",
                "strength": min(1.0, (rsi_value - 65) / 35 + (stoch_k - 75) / 25),
                "confidence": 0.6,
                "reasoning": f"Scalping sell: RSI ({rsi_value:.2f}) and Stochastic ({stoch_k:.2f}) overbought",
                "quantity": self._calculate_position_size(strategy, df["close"].iloc[-1])
            }
        
        return None
    
    async def _execute_swing_strategy(
        self, 
        strategy: Strategy, 
        df: pd.DataFrame, 
        indicators: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute swing trading strategy."""
        
        # Get trend indicators
        sma_20 = indicators.get("SMA_20")
        sma_50 = indicators.get("SMA_50")
        ema_12 = indicators.get("EMA_12")
        ema_26 = indicators.get("EMA_26")
        
        if not all([sma_20, sma_50, ema_12, ema_26]):
            return None
        
        current_price = df["close"].iloc[-1]
        
        # Swing buy: Price above both SMAs, EMAs in bullish alignment
        if (current_price > sma_20 > sma_50 and 
            ema_12 > ema_26):
            
            return {
                "type": "buy",
                "strength": 0.8,
                "confidence": 0.7,
                "reasoning": f"Swing buy: Price ({current_price:.2f}) above SMAs, EMAs bullish",
                "quantity": self._calculate_position_size(strategy, current_price)
            }
        
        # Swing sell: Price below both SMAs, EMAs in bearish alignment
        elif (current_price < sma_20 < sma_50 and 
              ema_12 < ema_26):
            
            return {
                "type": "sell",
                "strength": 0.8,
                "confidence": 0.7,
                "reasoning": f"Swing sell: Price ({current_price:.2f}) below SMAs, EMAs bearish",
                "quantity": self._calculate_position_size(strategy, current_price)
            }
        
        return None
    
    async def _execute_custom_strategy(
        self, 
        strategy: Strategy, 
        df: pd.DataFrame, 
        indicators: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute custom strategy based on configuration."""
        
        # TODO: Implement custom strategy logic
        # This would involve:
        # 1. Parsing strategy configuration
        # 2. Executing custom logic
        # 3. Generating signals based on custom rules
        
        return None
    
    def _calculate_position_size(self, strategy: Strategy, current_price: float) -> float:
        """Calculate position size based on strategy settings."""
        
        # Simple position sizing based on max position size percentage
        max_position_value = 10000  # $10,000 max position value
        position_value = max_position_value * (strategy.max_position_size / 100)
        quantity = position_value / current_price
        
        return quantity
    
    async def _execute_trade(
        self, 
        strategy: Strategy, 
        signal: Dict[str, Any], 
        symbol: str, 
        price: float, 
        db: Session
    ) -> None:
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
                
                # Send trade notification
                await notification_service.send_trade_notification(
                    user_id=strategy.user_id,
                    trade_data={
                        "symbol": symbol,
                        "side": side.value,
                        "quantity": float(signal["quantity"]),
                        "price": price,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info("Trade executed", order_id=order.id, symbol=symbol, side=side.value)
                
            except Exception as e:
                logger.error("Failed to execute trade", order_id=order.id, error=str(e))
                order.status = OrderStatus.REJECTED
                db.commit()
                
        except Exception as e:
            logger.error("Trade execution failed", strategy_id=strategy.id, error=str(e))


# Global strategy engine instance
strategy_engine = StrategyEngine()
