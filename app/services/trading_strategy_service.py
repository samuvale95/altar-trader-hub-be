"""
Trading Strategy Service for managing paper trading strategies
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import logging

# Add paper_trading to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'paper_trading'))

from app.models.trading_strategy import (
    TradingStrategy, BacktestResult, StrategyTrade, BacktestTrade, StrategyExecution,
    StrategyStatus, StrategyType, BacktestStatus
)
from app.schemas.trading_strategy import (
    TradingStrategyCreate, TradingStrategyUpdate, BacktestRequest,
    StrategyPerformanceMetrics, StrategyStatisticsResponse
)

logger = logging.getLogger(__name__)


class TradingStrategyService:
    """Service for managing trading strategies."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_strategy(self, user_id: int, strategy_data: TradingStrategyCreate) -> TradingStrategy:
        """Create a new trading strategy."""
        try:
            # Validate strategy parameters
            self._validate_strategy_parameters(strategy_data.strategy_type, strategy_data.parameters)
            
            # Create strategy
            strategy = TradingStrategy(
                user_id=user_id,
                name=strategy_data.name,
                description=strategy_data.description,
                strategy_type=strategy_data.strategy_type,
                parameters=strategy_data.parameters,
                symbol=strategy_data.symbol,
                timeframe=strategy_data.timeframe,
                initial_balance=strategy_data.initial_balance,
                commission_rate=strategy_data.commission_rate,
                auto_start=strategy_data.auto_start,
                current_balance=strategy_data.initial_balance,
                total_equity=strategy_data.initial_balance,
                status=StrategyStatus.INACTIVE
            )
            
            self.db.add(strategy)
            self.db.commit()
            self.db.refresh(strategy)
            
            # Log strategy creation
            self._log_strategy_execution(
                strategy_id=strategy.id,
                user_id=user_id,
                action="CREATE",
                status="SUCCESS",
                message=f"Strategy '{strategy.name}' created successfully"
            )
            
            logger.info(f"Created strategy {strategy.id} for user {user_id}")
            return strategy
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating strategy: {e}")
            raise
    
    def get_strategy(self, strategy_id: int, user_id: int) -> Optional[TradingStrategy]:
        """Get a strategy by ID."""
        return self.db.query(TradingStrategy).filter(
            TradingStrategy.id == strategy_id,
            TradingStrategy.user_id == user_id
        ).first()
    
    def get_strategies(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[StrategyStatus] = None
    ) -> List[TradingStrategy]:
        """Get user's strategies with pagination."""
        query = self.db.query(TradingStrategy).filter(TradingStrategy.user_id == user_id)
        
        if status:
            query = query.filter(TradingStrategy.status == status)
        
        return query.order_by(desc(TradingStrategy.created_at)).offset(skip).limit(limit).all()
    
    def update_strategy(
        self, 
        strategy_id: int, 
        user_id: int, 
        update_data: TradingStrategyUpdate
    ) -> Optional[TradingStrategy]:
        """Update a strategy."""
        try:
            strategy = self.get_strategy(strategy_id, user_id)
            if not strategy:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(strategy, field, value)
            
            strategy.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(strategy)
            
            # Log strategy update
            self._log_strategy_execution(
                strategy_id=strategy.id,
                user_id=user_id,
                action="UPDATE",
                status="SUCCESS",
                message=f"Strategy '{strategy.name}' updated successfully"
            )
            
            logger.info(f"Updated strategy {strategy_id} for user {user_id}")
            return strategy
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating strategy: {e}")
            raise
    
    def delete_strategy(self, strategy_id: int, user_id: int) -> bool:
        """Delete a strategy."""
        try:
            strategy = self.get_strategy(strategy_id, user_id)
            if not strategy:
                return False
            
            # Log strategy deletion
            self._log_strategy_execution(
                strategy_id=strategy.id,
                user_id=user_id,
                action="DELETE",
                status="SUCCESS",
                message=f"Strategy '{strategy.name}' deleted successfully"
            )
            
            self.db.delete(strategy)
            self.db.commit()
            
            logger.info(f"Deleted strategy {strategy_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting strategy: {e}")
            raise
    
    def start_strategy(self, strategy_id: int, user_id: int) -> bool:
        """Start a strategy."""
        try:
            strategy = self.get_strategy(strategy_id, user_id)
            if not strategy:
                return False
            
            if strategy.status == StrategyStatus.ACTIVE:
                return True  # Already active
            
            strategy.status = StrategyStatus.ACTIVE
            strategy.is_active = True
            strategy.started_at = datetime.utcnow()
            strategy.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log strategy start
            self._log_strategy_execution(
                strategy_id=strategy.id,
                user_id=user_id,
                action="START",
                status="SUCCESS",
                message=f"Strategy '{strategy.name}' started successfully",
                balance=strategy.current_balance,
                equity=strategy.total_equity,
                total_trades=strategy.total_trades
            )
            
            logger.info(f"Started strategy {strategy_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error starting strategy: {e}")
            raise
    
    def stop_strategy(self, strategy_id: int, user_id: int) -> bool:
        """Stop a strategy."""
        try:
            strategy = self.get_strategy(strategy_id, user_id)
            if not strategy:
                return False
            
            strategy.status = StrategyStatus.INACTIVE
            strategy.is_active = False
            strategy.stopped_at = datetime.utcnow()
            strategy.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log strategy stop
            self._log_strategy_execution(
                strategy_id=strategy.id,
                user_id=user_id,
                action="STOP",
                status="SUCCESS",
                message=f"Strategy '{strategy.name}' stopped successfully",
                balance=strategy.current_balance,
                equity=strategy.total_equity,
                total_trades=strategy.total_trades
            )
            
            logger.info(f"Stopped strategy {strategy_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error stopping strategy: {e}")
            raise
    
    def pause_strategy(self, strategy_id: int, user_id: int) -> bool:
        """Pause a strategy."""
        try:
            strategy = self.get_strategy(strategy_id, user_id)
            if not strategy:
                return False
            
            strategy.status = StrategyStatus.PAUSED
            strategy.is_active = False
            strategy.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log strategy pause
            self._log_strategy_execution(
                strategy_id=strategy.id,
                user_id=user_id,
                action="PAUSE",
                status="SUCCESS",
                message=f"Strategy '{strategy.name}' paused successfully",
                balance=strategy.current_balance,
                equity=strategy.total_equity,
                total_trades=strategy.total_trades
            )
            
            logger.info(f"Paused strategy {strategy_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error pausing strategy: {e}")
            raise
    
    def resume_strategy(self, strategy_id: int, user_id: int) -> bool:
        """Resume a strategy."""
        try:
            strategy = self.get_strategy(strategy_id, user_id)
            if not strategy:
                return False
            
            if strategy.status != StrategyStatus.PAUSED:
                return False
            
            strategy.status = StrategyStatus.ACTIVE
            strategy.is_active = True
            strategy.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log strategy resume
            self._log_strategy_execution(
                strategy_id=strategy.id,
                user_id=user_id,
                action="RESUME",
                status="SUCCESS",
                message=f"Strategy '{strategy.name}' resumed successfully",
                balance=strategy.current_balance,
                equity=strategy.total_equity,
                total_trades=strategy.total_trades
            )
            
            logger.info(f"Resumed strategy {strategy_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resuming strategy: {e}")
            raise
    
    def run_backtest(self, user_id: int, backtest_request: BacktestRequest) -> BacktestResult:
        """Run a backtest for a strategy."""
        try:
            # Get strategy
            strategy = self.get_strategy(backtest_request.strategy_id, user_id)
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
                status=BacktestStatus.PENDING
            )
            
            self.db.add(backtest)
            self.db.commit()
            self.db.refresh(backtest)
            
            # Start backtest execution (this would be done in background in production)
            self._execute_backtest(backtest)
            
            logger.info(f"Started backtest {backtest.id} for strategy {strategy.id}")
            return backtest
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error running backtest: {e}")
            raise
    
    def get_backtest_results(
        self, 
        user_id: int, 
        strategy_id: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[BacktestResult]:
        """Get backtest results."""
        query = self.db.query(BacktestResult).filter(BacktestResult.user_id == user_id)
        
        if strategy_id:
            query = query.filter(BacktestResult.strategy_id == strategy_id)
        
        return query.order_by(desc(BacktestResult.created_at)).offset(skip).limit(limit).all()
    
    def get_strategy_trades(
        self, 
        strategy_id: int, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[StrategyTrade]:
        """Get strategy trades."""
        return self.db.query(StrategyTrade).filter(
            StrategyTrade.strategy_id == strategy_id,
            StrategyTrade.user_id == user_id
        ).order_by(desc(StrategyTrade.executed_at)).offset(skip).limit(limit).all()
    
    def get_strategy_performance(self, strategy_id: int, user_id: int) -> StrategyPerformanceMetrics:
        """Get strategy performance metrics."""
        strategy = self.get_strategy(strategy_id, user_id)
        if not strategy:
            raise ValueError("Strategy not found")
        
        return StrategyPerformanceMetrics(
            total_return=strategy.total_return,
            annualized_return=0,  # Would need to calculate based on time period
            volatility=0,  # Would need to calculate from trades
            sharpe_ratio=strategy.sharpe_ratio,
            max_drawdown=strategy.max_drawdown,
            win_rate=strategy.win_rate,
            total_trades=strategy.total_trades,
            buy_trades=0,  # Would need to count from trades
            sell_trades=0,  # Would need to count from trades
            avg_trade_size=0,  # Would need to calculate from trades
            trade_frequency=0,  # Would need to calculate from trades
            current_balance=strategy.current_balance,
            total_equity=strategy.total_equity
        )
    
    def get_strategy_statistics(self, user_id: int) -> StrategyStatisticsResponse:
        """Get user's strategy statistics."""
        # Total strategies
        total_strategies = self.db.query(TradingStrategy).filter(
            TradingStrategy.user_id == user_id
        ).count()
        
        # Active strategies
        active_strategies = self.db.query(TradingStrategy).filter(
            TradingStrategy.user_id == user_id,
            TradingStrategy.status == StrategyStatus.ACTIVE
        ).count()
        
        # Total backtests
        total_backtests = self.db.query(BacktestResult).filter(
            BacktestResult.user_id == user_id
        ).count()
        
        # Running backtests
        running_backtests = self.db.query(BacktestResult).filter(
            BacktestResult.user_id == user_id,
            BacktestResult.status == BacktestStatus.RUNNING
        ).count()
        
        # Total trades
        total_trades = self.db.query(StrategyTrade).filter(
            StrategyTrade.user_id == user_id
        ).count()
        
        # Total profit (simplified calculation)
        strategies = self.db.query(TradingStrategy).filter(
            TradingStrategy.user_id == user_id
        ).all()
        
        total_profit = sum(strategy.total_return for strategy in strategies)
        
        # Best and worst strategies
        best_strategy = None
        worst_strategy = None
        
        if strategies:
            best_strategy = max(strategies, key=lambda s: s.total_return).name
            worst_strategy = min(strategies, key=lambda s: s.total_return).name
        
        return StrategyStatisticsResponse(
            total_strategies=total_strategies,
            active_strategies=active_strategies,
            total_backtests=total_backtests,
            running_backtests=running_backtests,
            total_trades=total_trades,
            total_profit=total_profit,
            best_strategy=best_strategy,
            worst_strategy=worst_strategy
        )
    
    def _validate_strategy_parameters(self, strategy_type: StrategyType, parameters: Dict[str, Any]):
        """Validate strategy-specific parameters."""
        # This would contain validation logic for each strategy type
        # For now, just check if parameters is a dict
        if not isinstance(parameters, dict):
            raise ValueError("Parameters must be a dictionary")
    
    def _log_strategy_execution(
        self, 
        strategy_id: int, 
        user_id: int, 
        action: str, 
        status: str, 
        message: str = None,
        balance: float = 0,
        equity: float = 0,
        total_trades: int = 0
    ):
        """Log strategy execution."""
        execution = StrategyExecution(
            strategy_id=strategy_id,
            user_id=user_id,
            action=action,
            status=status,
            message=message,
            balance=balance,
            equity=equity,
            total_trades=total_trades
        )
        
        self.db.add(execution)
        self.db.commit()
    
    def _execute_backtest(self, backtest: BacktestResult):
        """Execute backtest (simplified version)."""
        try:
            # Update status to running
            backtest.status = BacktestStatus.RUNNING
            backtest.started_at = datetime.utcnow()
            self.db.commit()
            
            # This is a simplified version - in production, this would:
            # 1. Download historical data
            # 2. Run the strategy
            # 3. Calculate metrics
            # 4. Save results
            
            # For now, just mark as completed with dummy data
            backtest.status = BacktestStatus.COMPLETED
            backtest.completed_at = datetime.utcnow()
            backtest.final_balance = backtest.initial_balance * 1.1  # 10% return
            backtest.total_equity = backtest.final_balance
            backtest.total_return = 0.1
            backtest.total_trades = 5
            backtest.win_rate = 0.6
            
            self.db.commit()
            
        except Exception as e:
            backtest.status = BacktestStatus.FAILED
            backtest.error_message = str(e)
            backtest.completed_at = datetime.utcnow()
            self.db.commit()
            logger.error(f"Backtest execution failed: {e}")
