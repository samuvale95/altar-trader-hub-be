"""
Paper Trading Integration Service
Integrates the paper trading system with the FastAPI backend
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add paper_trading to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'paper_trading'))

try:
    from paper_trading.core.data_feed import DataFeed, DataProcessor
    from paper_trading.core.backtest_engine import BacktestEngine
    from paper_trading.core.portfolio import VirtualPortfolio, OrderSide
    from paper_trading.strategies import StrategyFactory
    PAPER_TRADING_AVAILABLE = True
except ImportError as e:
    PAPER_TRADING_AVAILABLE = False
    logging.warning(f"Paper trading system not available: {e}")

from app.models.trading_strategy import (
    TradingStrategy, BacktestResult, StrategyTrade, BacktestTrade,
    StrategyStatus, BacktestStatus, StrategyType
)
from app.schemas.trading_strategy import BacktestRequest

logger = logging.getLogger(__name__)


class PaperTradingIntegrationService:
    """Service for integrating paper trading with the backend."""
    
    def __init__(self, db: Session):
        self.db = db
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        if not PAPER_TRADING_AVAILABLE:
            logger.warning("Paper trading system not available - some features will be limited")
    
    async def run_backtest_async(
        self, 
        backtest_request: BacktestRequest, 
        user_id: int
    ) -> BacktestResult:
        """Run backtest asynchronously."""
        if not PAPER_TRADING_AVAILABLE:
            raise ValueError("Paper trading system not available")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._run_backtest_sync, 
            backtest_request, 
            user_id
        )
    
    def _run_backtest_sync(self, backtest_request: BacktestRequest, user_id: int) -> BacktestResult:
        """Run backtest synchronously."""
        try:
            # Get strategy
            strategy = self.db.query(TradingStrategy).filter(
                TradingStrategy.id == backtest_request.strategy_id,
                TradingStrategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise ValueError("Strategy not found")
            
            # Create backtest result
            backtest = BacktestResult(
                strategy_id=strategy.id,
                user_id=user_id,
                name=backtest_request.name,
                description=backtest_request.description,
                start_date=backtest_request.start_date,
                end_date=backtest_request.end_date,
                symbol=backtest_request.symbol or strategy.symbol,
                timeframe=backtest_request.timeframe or strategy.timeframe,
                initial_balance=strategy.initial_balance,
                status=BacktestStatus.RUNNING
            )
            
            self.db.add(backtest)
            self.db.commit()
            self.db.refresh(backtest)
            
            # Update status to running
            backtest.status = BacktestStatus.RUNNING
            backtest.started_at = datetime.utcnow()
            self.db.commit()
            
            # Download data
            data_feed = DataFeed()
            data = data_feed.get_data(
                symbol=backtest.symbol,
                interval=backtest.timeframe,
                start_date=backtest.start_date.strftime('%Y-%m-%d'),
                end_date=backtest.end_date.strftime('%Y-%m-%d'),
                source='binance'
            )
            
            if data.empty:
                raise ValueError("No data available for the specified period")
            
            # Run backtest
            backtest_engine = BacktestEngine(
                initial_balance=float(strategy.initial_balance),
                commission_rate=float(strategy.commission_rate)
            )
            
            results = backtest_engine.run_backtest(
                data=data,
                strategy_name=strategy.strategy_type.value,
                strategy_parameters=strategy.parameters,
                symbol=backtest.symbol,
                start_date=backtest.start_date.strftime('%Y-%m-%d'),
                end_date=backtest.end_date.strftime('%Y-%m-%d')
            )
            
            # Update backtest with results
            self._update_backtest_with_results(backtest, results, data)
            
            # Save trades to database
            self._save_backtest_trades(backtest, results)
            
            logger.info(f"Backtest {backtest.id} completed successfully")
            return backtest
            
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}")
            
            # Update backtest with error
            if 'backtest' in locals():
                backtest.status = BacktestStatus.FAILED
                backtest.error_message = str(e)
                backtest.completed_at = datetime.utcnow()
                self.db.commit()
            
            raise
    
    def _update_backtest_with_results(self, backtest: BacktestResult, results: Dict, data: pd.DataFrame):
        """Update backtest with results."""
        try:
            # Update basic metrics
            backtest.status = BacktestStatus.COMPLETED
            backtest.completed_at = datetime.utcnow()
            backtest.total_periods = len(data)
            
            # Portfolio summary
            portfolio_summary = results.get('portfolio_summary', {})
            backtest.final_balance = portfolio_summary.get('current_balance', backtest.initial_balance)
            backtest.total_equity = portfolio_summary.get('total_equity', backtest.initial_balance)
            
            # Performance metrics
            metrics = results.get('metrics', {})
            backtest.total_return = metrics.get('total_return', 0)
            backtest.annualized_return = metrics.get('annualized_return', 0)
            backtest.volatility = metrics.get('volatility', 0)
            backtest.sharpe_ratio = metrics.get('sharpe_ratio', 0)
            backtest.max_drawdown = metrics.get('max_drawdown', 0)
            backtest.win_rate = metrics.get('win_rate', 0)
            
            # Trading statistics
            additional_metrics = results.get('additional_metrics', {})
            backtest.total_trades = additional_metrics.get('total_trades', 0)
            backtest.buy_trades = additional_metrics.get('buy_trades', 0)
            backtest.sell_trades = additional_metrics.get('sell_trades', 0)
            backtest.buy_hold_return = additional_metrics.get('buy_hold_return', 0)
            backtest.outperformance = additional_metrics.get('outperformance', 0)
            backtest.avg_trade_size = additional_metrics.get('avg_trade_size', 0)
            backtest.trade_frequency = additional_metrics.get('trade_frequency', 0)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating backtest results: {e}")
            raise
    
    def _save_backtest_trades(self, backtest: BacktestResult, results: Dict):
        """Save backtest trades to database."""
        try:
            trades_df = results.get('trades')
            if trades_df is None or trades_df.empty:
                return
            
            trades_to_save = []
            for _, trade in trades_df.iterrows():
                backtest_trade = BacktestTrade(
                    backtest_id=backtest.id,
                    symbol=trade.get('symbol', backtest.symbol),
                    side=trade.get('side', 'BUY'),
                    quantity=trade.get('quantity', 0),
                    price=trade.get('price', 0),
                    commission=trade.get('commission', 0),
                    signal_strength=trade.get('strength', 0),
                    reason=trade.get('reason', ''),
                    executed_at=trade.get('timestamp', datetime.utcnow())
                )
                trades_to_save.append(backtest_trade)
            
            self.db.add_all(trades_to_save)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error saving backtest trades: {e}")
            # Don't raise - this is not critical
    
    async def execute_strategy_live(
        self, 
        strategy_id: int, 
        user_id: int
    ) -> bool:
        """Execute strategy in live mode (simplified)."""
        if not PAPER_TRADING_AVAILABLE:
            raise ValueError("Paper trading system not available")
        
        try:
            # Get strategy
            strategy = self.db.query(TradingStrategy).filter(
                TradingStrategy.id == strategy_id,
                TradingStrategy.user_id == user_id
            ).first()
            
            if not strategy:
                return False
            
            # This would implement live strategy execution
            # For now, just log the execution
            logger.info(f"Executing strategy {strategy_id} for user {user_id}")
            
            # Update last run time
            strategy.last_run_at = datetime.utcnow()
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing strategy live: {e}")
            return False
    
    def get_strategy_performance_data(
        self, 
        strategy_id: int, 
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get strategy performance data for visualization."""
        try:
            # Get strategy
            strategy = self.db.query(TradingStrategy).filter(
                TradingStrategy.id == strategy_id,
                TradingStrategy.user_id == user_id
            ).first()
            
            if not strategy:
                return {}
            
            # Get recent trades
            trades = self.db.query(StrategyTrade).filter(
                StrategyTrade.strategy_id == strategy_id,
                StrategyTrade.user_id == user_id,
                StrategyTrade.executed_at >= datetime.utcnow() - timedelta(days=days)
            ).order_by(StrategyTrade.executed_at).all()
            
            # Calculate performance metrics
            total_trades = len(trades)
            buy_trades = len([t for t in trades if t.side == 'BUY'])
            sell_trades = len([t for t in trades if t.side == 'SELL'])
            
            # Calculate P&L (simplified)
            pnl = 0
            for trade in trades:
                if trade.side == 'BUY':
                    pnl -= float(trade.quantity * trade.price + trade.commission)
                else:  # SELL
                    pnl += float(trade.quantity * trade.price - trade.commission)
            
            return {
                'strategy_id': strategy_id,
                'strategy_name': strategy.name,
                'total_trades': total_trades,
                'buy_trades': buy_trades,
                'sell_trades': sell_trades,
                'current_balance': float(strategy.current_balance),
                'total_equity': float(strategy.total_equity),
                'total_return': float(strategy.total_return),
                'win_rate': float(strategy.win_rate),
                'max_drawdown': float(strategy.max_drawdown),
                'sharpe_ratio': float(strategy.sharpe_ratio),
                'pnl': pnl,
                'trades': [
                    {
                        'id': trade.id,
                        'symbol': trade.symbol,
                        'side': trade.side,
                        'quantity': float(trade.quantity),
                        'price': float(trade.price),
                        'commission': float(trade.commission),
                        'executed_at': trade.executed_at.isoformat(),
                        'reason': trade.reason
                    }
                    for trade in trades
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy performance data: {e}")
            return {}
    
    def get_available_strategies_info(self) -> List[Dict[str, Any]]:
        """Get information about available strategies."""
        if not PAPER_TRADING_AVAILABLE:
            return []
        
        try:
            from paper_trading.strategies import StrategyFactory
            return StrategyFactory.get_all_strategies_info()
        except Exception as e:
            logger.error(f"Error getting available strategies info: {e}")
            return []
    
    def validate_strategy_parameters(
        self, 
        strategy_type: StrategyType, 
        parameters: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validate strategy parameters."""
        if not PAPER_TRADING_AVAILABLE:
            return False, "Paper trading system not available"
        
        try:
            # Create strategy instance to validate parameters
            strategy = StrategyFactory.create_strategy(
                strategy_type.value, 
                parameters
            )
            
            # Test with mock data
            mock_data = self._create_mock_data()
            signals = strategy.generate_signals(mock_data)
            
            return True, "Parameters are valid"
            
        except Exception as e:
            return False, f"Invalid parameters: {str(e)}"
    
    def _create_mock_data(self) -> pd.DataFrame:
        """Create mock data for parameter validation."""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        mock_data = pd.DataFrame({
            'open': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(150, 250, 100),
            'low': np.random.uniform(50, 150, 100),
            'close': np.random.uniform(100, 200, 100),
            'volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
        
        # Add technical indicators
        processor = DataProcessor()
        return processor.add_technical_indicators(mock_data)
    
    def __del__(self):
        """Cleanup executor."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
