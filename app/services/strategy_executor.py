"""
Strategy execution service for running trading strategies.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.trading_strategy import TradingStrategy, StrategyStatus, StrategyType
from app.services.paper_trading_integration import PaperTradingIntegrationService
from app.services.data_feeder import data_feeder

logger = get_logger(__name__)


class StrategyExecutor:
    """Service for executing trading strategies."""
    
    def __init__(self):
        self.running_strategies: Dict[int, asyncio.Task] = {}
    
    async def start_strategy(self, strategy_id: int) -> bool:
        """Start a trading strategy."""
        
        db = SessionLocal()
        try:
            strategy = db.query(TradingStrategy).filter(TradingStrategy.id == strategy_id).first()
            if not strategy:
                logger.error(f"Strategy {strategy_id} not found")
                return False
            
            if strategy.is_active:
                logger.warning(f"Strategy {strategy_id} is already active")
                return True
            
            # Update strategy status
            strategy.is_active = True
            strategy.status = StrategyStatus.ACTIVE
            strategy.started_at = datetime.utcnow()
            db.commit()
            
            # Start strategy execution task
            task = asyncio.create_task(self._run_strategy(strategy_id))
            self.running_strategies[strategy_id] = task
            
            logger.info(f"Started strategy {strategy_id}: {strategy.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start strategy {strategy_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    async def stop_strategy(self, strategy_id: int) -> bool:
        """Stop a trading strategy."""
        
        db = SessionLocal()
        try:
            strategy = db.query(TradingStrategy).filter(TradingStrategy.id == strategy_id).first()
            if not strategy:
                logger.error(f"Strategy {strategy_id} not found")
                return False
            
            if not strategy.is_active:
                logger.warning(f"Strategy {strategy_id} is not active")
                return True
            
            # Update strategy status
            strategy.is_active = False
            strategy.status = StrategyStatus.INACTIVE
            strategy.stopped_at = datetime.utcnow()
            db.commit()
            
            # Cancel running task
            if strategy_id in self.running_strategies:
                task = self.running_strategies[strategy_id]
                task.cancel()
                del self.running_strategies[strategy_id]
            
            logger.info(f"Stopped strategy {strategy_id}: {strategy.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop strategy {strategy_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    async def _run_strategy(self, strategy_id: int):
        """Run a trading strategy continuously."""
        
        db = SessionLocal()
        try:
            strategy = db.query(TradingStrategy).filter(TradingStrategy.id == strategy_id).first()
            if not strategy:
                logger.error(f"Strategy {strategy_id} not found")
                return
            
            logger.info(f"Running strategy {strategy_id}: {strategy.name}")
            
            # Parse strategy parameters
            try:
                params = json.loads(strategy.parameters) if strategy.parameters else {}
            except json.JSONDecodeError:
                logger.error(f"Invalid parameters for strategy {strategy_id}")
                return
            
            # Get symbol and timeframe
            symbol = params.get('symbol', 'BTCUSDT')
            timeframe = params.get('timeframe', '1d')
            
            # Run strategy execution loop
            while strategy.is_active:
                try:
                    # Check if strategy is still active
                    db.refresh(strategy)
                    if not strategy.is_active:
                        break
                    
                    # Execute strategy
                    await self._execute_strategy_step(strategy, params)
                    
                    # Update last run time
                    strategy.last_run_at = datetime.utcnow()
                    db.commit()
                    
                    # Wait before next execution (based on timeframe)
                    wait_seconds = self._get_wait_seconds(timeframe)
                    await asyncio.sleep(wait_seconds)
                    
                except asyncio.CancelledError:
                    logger.info(f"Strategy {strategy_id} execution cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error executing strategy {strategy_id}: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retry
            
            logger.info(f"Strategy {strategy_id} execution completed")
            
        except Exception as e:
            logger.error(f"Failed to run strategy {strategy_id}: {e}")
        finally:
            db.close()
    
    async def _execute_strategy_step(self, strategy: TradingStrategy, params: Dict):
        """Execute a single step of the strategy."""
        
        try:
            symbol = params.get('symbol', 'BTCUSDT')
            timeframe = params.get('timeframe', '1d')
            
            # Get latest market data
            market_data = await data_feeder.get_latest_data(symbol, timeframe)
            if not market_data:
                logger.warning(f"No market data available for {symbol} {timeframe}")
                return
            
            # Execute strategy based on type
            if strategy.strategy_type == StrategyType.MA_CROSSOVER:
                await self._execute_ma_crossover(strategy, params, market_data)
            elif strategy.strategy_type == StrategyType.RSI_TRADING:
                await self._execute_rsi_trading(strategy, params, market_data)
            elif strategy.strategy_type == StrategyType.MACD_TRADING:
                await self._execute_macd_trading(strategy, params, market_data)
            elif strategy.strategy_type == StrategyType.DCA:
                await self._execute_dca(strategy, params, market_data)
            else:
                logger.warning(f"Unknown strategy type: {strategy.strategy_type}")
                
        except Exception as e:
            logger.error(f"Error executing strategy step: {e}")
    
    async def _execute_ma_crossover(self, strategy: TradingStrategy, params: Dict, market_data: List):
        """Execute MA Crossover strategy."""
        
        if len(market_data) < 2:
            return
        
        # Get short and long periods
        short_period = params.get('short_period', 10)
        long_period = params.get('long_period', 20)
        
        if len(market_data) < long_period:
            return
        
        # Calculate moving averages
        closes = [float(candle['close_price']) for candle in market_data[-long_period:]]
        short_ma = sum(closes[-short_period:]) / short_period
        long_ma = sum(closes) / long_period
        
        # Get previous values for crossover detection
        if len(market_data) >= long_period + 1:
            prev_closes = [float(candle['close_price']) for candle in market_data[-(long_period+1):-1]]
            prev_short_ma = sum(prev_closes[-short_period:]) / short_period
            prev_long_ma = sum(prev_closes) / long_period
            
            # Check for crossover
            if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                # Bullish crossover - buy signal
                await self._execute_buy(strategy, market_data[-1])
            elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
                # Bearish crossover - sell signal
                await self._execute_sell(strategy, market_data[-1])
    
    async def _execute_rsi_trading(self, strategy: TradingStrategy, params: Dict, market_data: List):
        """Execute RSI Trading strategy."""
        
        if len(market_data) < 14:  # RSI needs at least 14 periods
            return
        
        # Calculate RSI
        closes = [float(candle['close_price']) for candle in market_data[-14:]]
        rsi = self._calculate_rsi(closes)
        
        # RSI trading logic
        if rsi < 30:  # Oversold - buy signal
            await self._execute_buy(strategy, market_data[-1])
        elif rsi > 70:  # Overbought - sell signal
            await self._execute_sell(strategy, market_data[-1])
    
    async def _execute_macd_trading(self, strategy: TradingStrategy, params: Dict, market_data: List):
        """Execute MACD Trading strategy."""
        
        if len(market_data) < 26:  # MACD needs at least 26 periods
            return
        
        # Calculate MACD
        closes = [float(candle['close_price']) for candle in market_data[-26:]]
        macd_line, signal_line = self._calculate_macd(closes)
        
        # MACD trading logic
        if macd_line > signal_line and macd_line > 0:
            await self._execute_buy(strategy, market_data[-1])
        elif macd_line < signal_line and macd_line < 0:
            await self._execute_sell(strategy, market_data[-1])
    
    async def _execute_dca(self, strategy: TradingStrategy, params: Dict, market_data: List):
        """Execute Dollar Cost Averaging strategy."""
        
        # DCA logic - buy at regular intervals
        current_time = datetime.utcnow()
        last_buy = strategy.last_run_at or strategy.started_at
        
        # Check if enough time has passed for next DCA buy
        interval_hours = params.get('interval_hours', 24)
        if (current_time - last_buy).total_seconds() >= interval_hours * 3600:
            await self._execute_buy(strategy, market_data[-1])
    
    async def _execute_buy(self, strategy: TradingStrategy, candle: Dict):
        """Execute a buy order."""
        
        try:
            # Calculate position size
            risk_per_trade = float(strategy.parameters.get('risk_per_trade', 0.02)) if strategy.parameters else 0.02
            position_size = float(strategy.current_balance) * risk_per_trade
            price = float(candle['close_price'])
            quantity = position_size / price
            
            # Update strategy balance
            strategy.current_balance = float(strategy.current_balance) - position_size
            strategy.total_trades += 1
            
            logger.info(f"Strategy {strategy.id} BUY: {quantity:.6f} at {price:.2f}")
            
        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
    
    async def _execute_sell(self, strategy: TradingStrategy, candle: Dict):
        """Execute a sell order."""
        
        try:
            # For simplicity, we'll just log the sell signal
            # In a real implementation, you'd track positions and calculate P&L
            price = float(candle['close_price'])
            
            logger.info(f"Strategy {strategy.id} SELL signal at {price:.2f}")
            
        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate RSI indicator."""
        
        if len(closes) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, closes: List[float]) -> tuple:
        """Calculate MACD indicator."""
        
        # Simple MACD calculation
        ema_12 = self._calculate_ema(closes, 12)
        ema_26 = self._calculate_ema(closes, 26)
        macd_line = ema_12 - ema_26
        
        # Signal line (9-period EMA of MACD)
        signal_line = macd_line  # Simplified
        
        return macd_line, signal_line
    
    def _calculate_ema(self, closes: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        
        if len(closes) < period:
            return sum(closes) / len(closes)
        
        multiplier = 2 / (period + 1)
        ema = closes[0]
        
        for i in range(1, len(closes)):
            ema = (closes[i] * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _get_wait_seconds(self, timeframe: str) -> int:
        """Get wait time in seconds based on timeframe."""
        
        timeframe_map = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        
        return timeframe_map.get(timeframe, 3600)  # Default to 1 hour
    
    async def start_all_active_strategies(self):
        """Start all active strategies."""
        
        db = SessionLocal()
        try:
            active_strategies = db.query(TradingStrategy).filter(
                TradingStrategy.is_active == True
            ).all()
            
            for strategy in active_strategies:
                await self.start_strategy(strategy.id)
                
            logger.info(f"Started {len(active_strategies)} active strategies")
            
        except Exception as e:
            logger.error(f"Failed to start active strategies: {e}")
        finally:
            db.close()
    
    async def stop_all_strategies(self):
        """Stop all running strategies."""
        
        for strategy_id in list(self.running_strategies.keys()):
            await self.stop_strategy(strategy_id)
        
        logger.info("Stopped all strategies")


# Global strategy executor instance
strategy_executor = StrategyExecutor()
