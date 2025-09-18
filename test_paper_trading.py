#!/usr/bin/env python3
"""
Test script for Paper Trading System
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add paper_trading to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'paper_trading'))

def test_data_feed():
    """Test data feed functionality."""
    print("Testing Data Feed...")
    
    try:
        from paper_trading.core.data_feed import DataFeed, DataProcessor
        
        # Test with mock data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        mock_data = pd.DataFrame({
            'open': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(150, 250, 100),
            'low': np.random.uniform(50, 150, 100),
            'close': np.random.uniform(100, 200, 100),
            'volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
        
        # Test technical indicators
        processor = DataProcessor()
        data_with_indicators = processor.add_technical_indicators(mock_data)
        data_with_returns = processor.calculate_returns(data_with_indicators)
        
        print("✅ Data Feed: OK")
        print(f"   - Data shape: {data_with_indicators.shape}")
        print(f"   - Indicators added: {len([col for col in data_with_indicators.columns if col not in ['open', 'high', 'low', 'close', 'volume']])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data Feed: ERROR - {e}")
        return False

def test_portfolio():
    """Test portfolio functionality."""
    print("\nTesting Portfolio...")
    
    try:
        from paper_trading.core.portfolio import VirtualPortfolio, OrderSide, OrderType
        
        # Create portfolio
        portfolio = VirtualPortfolio(initial_balance=10000.0)
        
        # Test placing orders
        order_id = portfolio.place_order(
            symbol='BTCUSDT',
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            order_type=OrderType.LIMIT,
            strategy='test',
            reason='Test order'
        )
        
        # Test executing order
        success = portfolio.execute_order(order_id, 50000.0)
        
        # Test portfolio summary
        summary = portfolio.get_portfolio_summary({'BTCUSDT': 50000.0})
        
        print("✅ Portfolio: OK")
        print(f"   - Order placed: {order_id}")
        print(f"   - Order executed: {success}")
        print(f"   - Balance: ${summary['current_balance']:.2f}")
        print(f"   - Equity: ${summary['total_equity']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio: ERROR - {e}")
        return False

def test_strategies():
    """Test strategy functionality."""
    print("\nTesting Strategies...")
    
    try:
        from paper_trading.strategies import StrategyFactory
        
        # Test strategy factory
        available_strategies = StrategyFactory.get_available_strategies()
        print(f"   - Available strategies: {len(available_strategies)}")
        
        # Test creating strategies
        for strategy_name in ['dca', 'rsi', 'macd']:
            strategy = StrategyFactory.create_strategy(strategy_name)
            print(f"   - {strategy_name}: {strategy.name}")
        
        # Test RSI strategy with mock data
        rsi_strategy = StrategyFactory.create_strategy('rsi')
        
        # Create mock data
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        mock_data = pd.DataFrame({
            'open': np.random.uniform(100, 200, 50),
            'high': np.random.uniform(150, 250, 50),
            'low': np.random.uniform(50, 150, 50),
            'close': np.random.uniform(100, 200, 50),
            'volume': np.random.uniform(1000, 10000, 50)
        }, index=dates)
        
        # Add RSI indicator
        from paper_trading.core.data_feed import DataProcessor
        processor = DataProcessor()
        mock_data = processor.add_technical_indicators(mock_data)
        
        # Generate signals
        signals = rsi_strategy.generate_signals(mock_data)
        
        print("✅ Strategies: OK")
        print(f"   - Signals generated: {len(signals[signals['signal'] != 0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategies: ERROR - {e}")
        return False

def test_backtest_engine():
    """Test backtest engine."""
    print("\nTesting Backtest Engine...")
    
    try:
        from paper_trading.core.backtest_engine import BacktestEngine
        from paper_trading.core.data_feed import DataProcessor
        
        # Create mock data
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
        mock_data = processor.add_technical_indicators(mock_data)
        mock_data = processor.calculate_returns(mock_data)
        
        # Create backtest engine
        backtest_engine = BacktestEngine(initial_balance=10000.0)
        
        # Run backtest
        results = backtest_engine.run_backtest(
            data=mock_data,
            strategy_name='rsi',
            strategy_parameters={'rsi_period': 14, 'oversold_threshold': 30, 'overbought_threshold': 70},
            symbol='BTCUSDT'
        )
        
        print("✅ Backtest Engine: OK")
        print(f"   - Total trades: {results['additional_metrics'].get('total_trades', 0)}")
        print(f"   - Total return: {results['metrics'].get('total_return_pct', 0):.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Backtest Engine: ERROR - {e}")
        return False

def test_reporting():
    """Test reporting functionality."""
    print("\nTesting Reporting...")
    
    try:
        from paper_trading.core.reporting import TradingReporter
        
        # Create mock results
        mock_results = {
            'strategy_name': 'Test Strategy',
            'symbol': 'BTCUSDT',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'total_periods': 365,
            'portfolio_summary': {
                'initial_balance': 10000.0,
                'current_balance': 5000.0,
                'total_equity': 12000.0,
                'total_return_pct': 20.0
            },
            'metrics': {
                'total_return_pct': 20.0,
                'sharpe_ratio': 1.5,
                'max_drawdown_pct': -10.0,
                'win_rate_pct': 60.0
            },
            'additional_metrics': {
                'total_trades': 50,
                'buy_trades': 25,
                'sell_trades': 25
            },
            'trades': pd.DataFrame(),
            'orders': pd.DataFrame(),
            'equity_curve': []
        }
        
        # Test reporter
        reporter = TradingReporter()
        summary = reporter.generate_summary_report(mock_results)
        
        print("✅ Reporting: OK")
        print(f"   - Summary length: {len(summary)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Reporting: ERROR - {e}")
        return False

def main():
    """Run all tests."""
    print("PAPER TRADING SYSTEM - TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_data_feed,
        test_portfolio,
        test_strategies,
        test_backtest_engine,
        test_reporting
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"TEST RESULTS: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
