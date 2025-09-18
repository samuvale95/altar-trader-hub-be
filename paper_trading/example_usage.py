#!/usr/bin/env python3
"""
Example usage of the Paper Trading System
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.data_feed import DataFeed, DataProcessor
from core.backtest_engine import BacktestEngine
from core.reporting import TradingReporter
from strategies import StrategyFactory


def example_single_strategy():
    """Example: Run a single strategy backtest."""
    print("=" * 60)
    print("EXAMPLE: Single Strategy Backtest")
    print("=" * 60)
    
    # 1. Download data
    print("1. Downloading data...")
    data_feed = DataFeed()
    data = data_feed.get_data(
        symbol='BTCUSDT',
        interval='1d',
        start_date='2023-01-01',
        end_date='2024-01-01',
        source='binance'
    )
    print(f"   Downloaded {len(data)} records")
    
    # 2. Run RSI strategy
    print("\n2. Running RSI strategy...")
    backtest_engine = BacktestEngine(initial_balance=10000.0)
    
    rsi_parameters = {
        'rsi_period': 14,
        'oversold_threshold': 30,
        'overbought_threshold': 70
    }
    
    results = backtest_engine.run_backtest(
        data=data,
        strategy_name='rsi',
        strategy_parameters=rsi_parameters,
        symbol='BTCUSDT'
    )
    
    # 3. Display results
    print("\n3. Results:")
    reporter = TradingReporter()
    summary = reporter.generate_summary_report(results)
    print(summary)
    
    return results


def example_strategy_comparison():
    """Example: Compare multiple strategies."""
    print("=" * 60)
    print("EXAMPLE: Strategy Comparison")
    print("=" * 60)
    
    # 1. Download data
    print("1. Downloading data...")
    data_feed = DataFeed()
    data = data_feed.get_data(
        symbol='BTCUSDT',
        interval='1d',
        start_date='2023-01-01',
        end_date='2024-01-01',
        source='binance'
    )
    print(f"   Downloaded {len(data)} records")
    
    # 2. Define strategies to compare
    strategies = [
        {'name': 'dca', 'parameters': {'investment_amount': 100, 'frequency': 7}},
        {'name': 'rsi', 'parameters': {'rsi_period': 14, 'oversold_threshold': 30, 'overbought_threshold': 70}},
        {'name': 'macd', 'parameters': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}},
        {'name': 'ma_crossover', 'parameters': {'fast_period': 10, 'slow_period': 30}}
    ]
    
    # 3. Run comparison
    print("\n2. Running strategy comparison...")
    backtest_engine = BacktestEngine(initial_balance=10000.0)
    
    comparison_df = backtest_engine.compare_strategies(
        data=data,
        strategies=strategies,
        symbol='BTCUSDT'
    )
    
    # 4. Display results
    print("\n3. Comparison Results:")
    print(comparison_df.to_string(index=False))
    
    return comparison_df


def example_custom_strategy():
    """Example: Create and test a custom strategy."""
    print("=" * 60)
    print("EXAMPLE: Custom Strategy")
    print("=" * 60)
    
    # 1. Download data
    print("1. Downloading data...")
    data_feed = DataFeed()
    data = data_feed.get_data(
        symbol='ETHUSDT',
        interval='1h',
        start_date='2024-01-01',
        end_date='2024-02-01',
        source='binance'
    )
    print(f"   Downloaded {len(data)} records")
    
    # 2. Test different RSI parameters
    print("\n2. Testing different RSI parameters...")
    
    rsi_configs = [
        {'name': 'RSI Conservative', 'parameters': {'rsi_period': 14, 'oversold_threshold': 25, 'overbought_threshold': 75}},
        {'name': 'RSI Aggressive', 'parameters': {'rsi_period': 14, 'oversold_threshold': 35, 'overbought_threshold': 65}},
        {'name': 'RSI Long Period', 'parameters': {'rsi_period': 21, 'oversold_threshold': 30, 'overbought_threshold': 70}}
    ]
    
    backtest_engine = BacktestEngine(initial_balance=10000.0)
    
    results = []
    for config in rsi_configs:
        print(f"   Testing {config['name']}...")
        
        result = backtest_engine.run_backtest(
            data=data,
            strategy_name='rsi',
            strategy_parameters=config['parameters'],
            symbol='ETHUSDT'
        )
        
        results.append({
            'Strategy': config['name'],
            'Total Return %': result['metrics'].get('total_return_pct', 0),
            'Sharpe Ratio': result['metrics'].get('sharpe_ratio', 0),
            'Max Drawdown %': result['metrics'].get('max_drawdown_pct', 0),
            'Total Trades': result['additional_metrics'].get('total_trades', 0)
        })
    
    # 3. Display results
    print("\n3. Parameter Comparison Results:")
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    
    return results_df


def example_data_analysis():
    """Example: Analyze market data."""
    print("=" * 60)
    print("EXAMPLE: Data Analysis")
    print("=" * 60)
    
    # 1. Download data
    print("1. Downloading data...")
    data_feed = DataFeed()
    data = data_feed.get_data(
        symbol='BTCUSDT',
        interval='1d',
        start_date='2023-01-01',
        end_date='2024-01-01',
        source='binance'
    )
    print(f"   Downloaded {len(data)} records")
    
    # 2. Add technical indicators
    print("\n2. Adding technical indicators...")
    data = DataProcessor.add_technical_indicators(data)
    data = DataProcessor.calculate_returns(data)
    
    # 3. Basic statistics
    print("\n3. Basic Statistics:")
    print(f"   Price Range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    print(f"   Average Daily Return: {data['returns'].mean()*100:.2f}%")
    print(f"   Daily Volatility: {data['returns'].std()*100:.2f}%")
    print(f"   Total Return: {data['cumulative_returns'].iloc[-1]*100:.2f}%")
    
    # 4. RSI analysis
    print(f"\n4. RSI Analysis:")
    print(f"   RSI Range: {data['rsi'].min():.1f} - {data['rsi'].max():.1f}")
    print(f"   Oversold periods: {(data['rsi'] < 30).sum()}")
    print(f"   Overbought periods: {(data['rsi'] > 70).sum()}")
    
    return data


def main():
    """Run all examples."""
    print("PAPER TRADING SYSTEM - EXAMPLES")
    print("=" * 60)
    
    try:
        # Example 1: Single strategy
        example_single_strategy()
        
        print("\n" + "=" * 60)
        input("Press Enter to continue to next example...")
        
        # Example 2: Strategy comparison
        example_strategy_comparison()
        
        print("\n" + "=" * 60)
        input("Press Enter to continue to next example...")
        
        # Example 3: Custom strategy
        example_custom_strategy()
        
        print("\n" + "=" * 60)
        input("Press Enter to continue to next example...")
        
        # Example 4: Data analysis
        example_data_analysis()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
