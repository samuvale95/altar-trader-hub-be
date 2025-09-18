#!/usr/bin/env python3
"""
Paper Trading System - Main Script
Simulates crypto trading strategies without real money
"""

import argparse
import logging
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.data_feed import DataFeed, DataProcessor
from core.backtest_engine import BacktestEngine
from core.reporting import TradingReporter
from strategies import StrategyFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function for paper trading system."""
    parser = argparse.ArgumentParser(description='Paper Trading System for Crypto Strategies')
    
    # Data parameters
    parser.add_argument('--symbol', default='BTCUSDT', help='Trading symbol (default: BTCUSDT)')
    parser.add_argument('--interval', default='1d', help='Time interval (default: 1d)')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--source', default='binance', choices=['binance', 'yahoo'], help='Data source')
    
    # Strategy parameters
    parser.add_argument('--strategy', required=True, help='Strategy name')
    parser.add_argument('--list-strategies', action='store_true', help='List available strategies')
    
    # Portfolio parameters
    parser.add_argument('--initial-balance', type=float, default=10000.0, help='Initial balance (default: 10000)')
    parser.add_argument('--commission', type=float, default=0.001, help='Commission rate (default: 0.001)')
    
    # Output parameters
    parser.add_argument('--output-dir', default='results', help='Output directory (default: results)')
    parser.add_argument('--save-data', action='store_true', help='Save downloaded data')
    parser.add_argument('--generate-plots', action='store_true', help='Generate plots')
    parser.add_argument('--html-report', action='store_true', help='Generate HTML report')
    
    # Comparison mode
    parser.add_argument('--compare', action='store_true', help='Compare all strategies')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # List strategies if requested
    if args.list_strategies:
        list_strategies()
        return
    
    # Set default dates if not provided
    if not args.start_date:
        args.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not args.end_date:
        args.end_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        if args.compare:
            run_strategy_comparison(args)
        else:
            run_single_strategy(args)
            
    except Exception as e:
        logger.error(f"Error running paper trading: {e}")
        sys.exit(1)


def list_strategies():
    """List all available strategies."""
    print("\nAvailable Trading Strategies:")
    print("=" * 50)
    
    strategies_info = StrategyFactory.get_all_strategies_info()
    
    for name, info in strategies_info.items():
        if 'error' not in info:
            print(f"\n{name.upper()}:")
            print(f"  Description: {info['description']}")
            print(f"  Default Parameters: {info['default_parameters']}")
        else:
            print(f"\n{name.upper()}: Error - {info['error']}")


def run_single_strategy(args):
    """Run a single strategy backtest."""
    logger.info(f"Running {args.strategy} strategy for {args.symbol}")
    
    # Download data
    data_feed = DataFeed()
    data = data_feed.get_data(
        symbol=args.symbol,
        interval=args.interval,
        start_date=args.start_date,
        end_date=args.end_date,
        source=args.source
    )
    
    if data.empty:
        logger.error("No data downloaded")
        return
    
    logger.info(f"Downloaded {len(data)} records")
    
    # Save data if requested
    if args.save_data:
        data_file = os.path.join(args.output_dir, f"{args.symbol}_{args.interval}_data.csv")
        data_feed.save_data(data, data_file)
    
    # Run backtest
    backtest_engine = BacktestEngine(
        initial_balance=args.initial_balance,
        commission_rate=args.commission
    )
    
    # Get strategy parameters (you can customize these)
    strategy_parameters = get_strategy_parameters(args.strategy)
    
    results = backtest_engine.run_backtest(
        data=data,
        strategy_name=args.strategy,
        strategy_parameters=strategy_parameters,
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    # Generate reports
    reporter = TradingReporter()
    
    # Print summary
    summary = reporter.generate_summary_report(results)
    print(summary)
    
    # Save results
    base_filename = os.path.join(args.output_dir, f"{args.strategy}_{args.symbol}_{args.interval}")
    backtest_engine.save_results(args.strategy, base_filename)
    
    # Generate plots
    if args.generate_plots:
        reporter.plot_equity_curve(results, f"{base_filename}_equity.png")
        reporter.plot_drawdown(results, f"{base_filename}_drawdown.png")
        reporter.plot_trades(results, f"{base_filename}_trades.png")
    
    # Generate HTML report
    if args.html_report:
        reporter.generate_html_report(results, f"{base_filename}_report.html")
    
    logger.info(f"Results saved to {args.output_dir}")


def run_strategy_comparison(args):
    """Run comparison of all strategies."""
    logger.info("Running strategy comparison")
    
    # Download data
    data_feed = DataFeed()
    data = data_feed.get_data(
        symbol=args.symbol,
        interval=args.interval,
        start_date=args.start_date,
        end_date=args.end_date,
        source=args.source
    )
    
    if data.empty:
        logger.error("No data downloaded")
        return
    
    # Get all available strategies
    available_strategies = StrategyFactory.get_available_strategies()
    
    # Prepare strategy configurations
    strategies = []
    for strategy_name in available_strategies:
        strategies.append({
            'name': strategy_name,
            'parameters': get_strategy_parameters(strategy_name)
        })
    
    # Run comparison
    backtest_engine = BacktestEngine(
        initial_balance=args.initial_balance,
        commission_rate=args.commission
    )
    
    comparison_df = backtest_engine.compare_strategies(
        data=data,
        strategies=strategies,
        symbol=args.symbol
    )
    
    # Print comparison results
    print("\nStrategy Comparison Results:")
    print("=" * 80)
    print(comparison_df.to_string(index=False))
    
    # Save comparison results
    comparison_file = os.path.join(args.output_dir, f"strategy_comparison_{args.symbol}.csv")
    comparison_df.to_csv(comparison_file, index=False)
    logger.info(f"Comparison results saved to {comparison_file}")
    
    # Generate comparison plots
    if args.generate_plots:
        reporter = TradingReporter()
        reporter.plot_strategy_comparison(comparison_df, f"{args.output_dir}/strategy_comparison.png")


def get_strategy_parameters(strategy_name: str) -> dict:
    """Get default parameters for a strategy."""
    # You can customize these parameters for each strategy
    default_params = {
        'dca': {
            'investment_amount': 100.0,
            'frequency': 7,
            'max_investments': 52
        },
        'rsi': {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70
        },
        'macd': {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        },
        'ma_crossover': {
            'fast_period': 10,
            'slow_period': 30,
            'ma_type': 'SMA'
        },
        'bollinger_bands': {
            'period': 20,
            'std_dev': 2.0
        },
        'range_trading': {
            'lookback_period': 20,
            'support_threshold': 0.02,
            'resistance_threshold': 0.02
        },
        'grid_trading': {
            'grid_size': 0.01,
            'grid_levels': 10
        },
        'fear_greed': {
            'fear_threshold': 25,
            'greed_threshold': 75
        }
    }
    
    return default_params.get(strategy_name, {})


if __name__ == "__main__":
    main()
