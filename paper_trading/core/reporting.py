"""
Reporting and Visualization for Paper Trading Results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TradingReporter:
    """Reporting and visualization for trading results."""
    
    def __init__(self):
        # Set matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def generate_summary_report(self, results: Dict) -> str:
        """Generate a text summary report."""
        if not results:
            return "No results available."
        
        report = []
        report.append("=" * 60)
        report.append("TRADING STRATEGY BACKTEST REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Basic info
        report.append(f"Strategy: {results.get('strategy_name', 'Unknown')}")
        report.append(f"Symbol: {results.get('symbol', 'Unknown')}")
        report.append(f"Period: {results.get('start_date', 'Unknown')} to {results.get('end_date', 'Unknown')}")
        report.append(f"Total Periods: {results.get('total_periods', 0)}")
        report.append("")
        
        # Portfolio summary
        portfolio = results.get('portfolio_summary', {})
        report.append("PORTFOLIO SUMMARY:")
        report.append("-" * 30)
        report.append(f"Initial Balance: ${portfolio.get('initial_balance', 0):,.2f}")
        report.append(f"Final Balance: ${portfolio.get('current_balance', 0):,.2f}")
        report.append(f"Total Equity: ${portfolio.get('total_equity', 0):,.2f}")
        report.append(f"Total Return: {portfolio.get('total_return_pct', 0):.2f}%")
        report.append("")
        
        # Performance metrics
        metrics = results.get('metrics', {})
        report.append("PERFORMANCE METRICS:")
        report.append("-" * 30)
        report.append(f"Total Return: {metrics.get('total_return_pct', 0):.2f}%")
        report.append(f"Annualized Return: {metrics.get('annualized_return_pct', 0):.2f}%")
        report.append(f"Volatility: {metrics.get('volatility_pct', 0):.2f}%")
        report.append(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
        report.append(f"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
        report.append("")
        
        # Trading statistics
        additional = results.get('additional_metrics', {})
        report.append("TRADING STATISTICS:")
        report.append("-" * 30)
        report.append(f"Total Trades: {additional.get('total_trades', 0)}")
        report.append(f"Buy Trades: {additional.get('buy_trades', 0)}")
        report.append(f"Sell Trades: {additional.get('sell_trades', 0)}")
        report.append(f"Win Rate: {metrics.get('win_rate_pct', 0):.2f}%")
        report.append(f"Avg Trade Size: {additional.get('avg_trade_size', 0):.6f}")
        report.append(f"Trades per Day: {additional.get('trades_per_day', 0):.2f}")
        report.append("")
        
        # Buy and hold comparison
        buy_hold = additional.get('buy_hold_return_pct', 0)
        strategy_return = metrics.get('total_return_pct', 0)
        outperformance = strategy_return - buy_hold
        
        report.append("BUY & HOLD COMPARISON:")
        report.append("-" * 30)
        report.append(f"Buy & Hold Return: {buy_hold:.2f}%")
        report.append(f"Strategy Return: {strategy_return:.2f}%")
        report.append(f"Outperformance: {outperformance:.2f}%")
        report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def plot_equity_curve(self, results: Dict, save_path: str = None):
        """Plot equity curve."""
        if not results or not results.get('equity_curve'):
            logger.warning("No equity curve data available")
            return
        
        equity_data = results['equity_curve']
        equity_df = pd.DataFrame(equity_data)
        equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
        
        plt.figure(figsize=(12, 6))
        plt.plot(equity_df['timestamp'], equity_df['equity'], linewidth=2, label='Portfolio Equity')
        
        # Add initial balance line
        initial_balance = results.get('portfolio_summary', {}).get('initial_balance', 0)
        plt.axhline(y=initial_balance, color='r', linestyle='--', alpha=0.7, label='Initial Balance')
        
        plt.title(f"Equity Curve - {results.get('strategy_name', 'Unknown Strategy')}")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value ($)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Equity curve saved to {save_path}")
        
        plt.show()
    
    def plot_drawdown(self, results: Dict, save_path: str = None):
        """Plot drawdown chart."""
        if not results or not results.get('equity_curve'):
            logger.warning("No equity curve data available")
            return
        
        equity_data = results['equity_curve']
        equity_df = pd.DataFrame(equity_data)
        equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
        
        # Calculate drawdown
        equity_df['running_max'] = equity_df['equity'].expanding().max()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['running_max']) / equity_df['running_max'] * 100
        
        plt.figure(figsize=(12, 6))
        plt.fill_between(equity_df['timestamp'], equity_df['drawdown'], 0, alpha=0.3, color='red')
        plt.plot(equity_df['timestamp'], equity_df['drawdown'], color='red', linewidth=1)
        
        plt.title(f"Drawdown Chart - {results.get('strategy_name', 'Unknown Strategy')}")
        plt.xlabel("Date")
        plt.ylabel("Drawdown (%)")
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Drawdown chart saved to {save_path}")
        
        plt.show()
    
    def plot_trades(self, results: Dict, save_path: str = None):
        """Plot trades on price chart."""
        if not results or not results.get('trades'):
            logger.warning("No trades data available")
            return
        
        trades_df = results['trades']
        if trades_df.empty:
            logger.warning("No trades to plot")
            return
        
        # This would require price data - simplified version
        plt.figure(figsize=(12, 6))
        
        # Plot buy trades
        buy_trades = trades_df[trades_df['side'] == 'BUY']
        if not buy_trades.empty:
            plt.scatter(buy_trades['timestamp'], buy_trades['price'], 
                       color='green', marker='^', s=100, label='Buy', alpha=0.7)
        
        # Plot sell trades
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        if not sell_trades.empty:
            plt.scatter(sell_trades['timestamp'], sell_trades['price'], 
                       color='red', marker='v', s=100, label='Sell', alpha=0.7)
        
        plt.title(f"Trades - {results.get('strategy_name', 'Unknown Strategy')}")
        plt.xlabel("Date")
        plt.ylabel("Price ($)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Trades chart saved to {save_path}")
        
        plt.show()
    
    def plot_strategy_comparison(self, comparison_df: pd.DataFrame, save_path: str = None):
        """Plot strategy comparison chart."""
        if comparison_df.empty:
            logger.warning("No comparison data available")
            return
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Total Return comparison
        axes[0, 0].bar(comparison_df['Strategy'], comparison_df['Total Return %'])
        axes[0, 0].set_title('Total Return Comparison')
        axes[0, 0].set_ylabel('Return (%)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Sharpe Ratio comparison
        axes[0, 1].bar(comparison_df['Strategy'], comparison_df['Sharpe Ratio'])
        axes[0, 1].set_title('Sharpe Ratio Comparison')
        axes[0, 1].set_ylabel('Sharpe Ratio')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Max Drawdown comparison
        axes[1, 0].bar(comparison_df['Strategy'], comparison_df['Max Drawdown %'])
        axes[1, 0].set_title('Max Drawdown Comparison')
        axes[1, 0].set_ylabel('Drawdown (%)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Win Rate comparison
        axes[1, 1].bar(comparison_df['Strategy'], comparison_df['Win Rate %'])
        axes[1, 1].set_title('Win Rate Comparison')
        axes[1, 1].set_ylabel('Win Rate (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Strategy comparison saved to {save_path}")
        
        plt.show()
    
    def export_results_to_csv(self, results: Dict, base_filename: str):
        """Export results to CSV files."""
        if not results:
            logger.warning("No results to export")
            return
        
        # Export trades
        if not results['trades'].empty:
            trades_file = f"{base_filename}_trades.csv"
            results['trades'].to_csv(trades_file, index=False)
            logger.info(f"Trades exported to {trades_file}")
        
        # Export orders
        if not results['orders'].empty:
            orders_file = f"{base_filename}_orders.csv"
            results['orders'].to_csv(orders_file, index=False)
            logger.info(f"Orders exported to {orders_file}")
        
        # Export equity curve
        if results['equity_curve']:
            equity_file = f"{base_filename}_equity.csv"
            equity_df = pd.DataFrame(results['equity_curve'])
            equity_df.to_csv(equity_file, index=False)
            logger.info(f"Equity curve exported to {equity_file}")
    
    def generate_html_report(self, results: Dict, output_file: str):
        """Generate HTML report."""
        if not results:
            logger.warning("No results to generate HTML report")
            return
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading Strategy Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e8f4f8; border-radius: 3px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Trading Strategy Backtest Report</h1>
                <p><strong>Strategy:</strong> {results.get('strategy_name', 'Unknown')}</p>
                <p><strong>Symbol:</strong> {results.get('symbol', 'Unknown')}</p>
                <p><strong>Period:</strong> {results.get('start_date', 'Unknown')} to {results.get('end_date', 'Unknown')}</p>
            </div>
            
            <div class="section">
                <h2>Performance Summary</h2>
                <div class="metric">Total Return: {results.get('metrics', {}).get('total_return_pct', 0):.2f}%</div>
                <div class="metric">Sharpe Ratio: {results.get('metrics', {}).get('sharpe_ratio', 0):.3f}</div>
                <div class="metric">Max Drawdown: {results.get('metrics', {}).get('max_drawdown_pct', 0):.2f}%</div>
                <div class="metric">Win Rate: {results.get('metrics', {}).get('win_rate_pct', 0):.2f}%</div>
            </div>
            
            <div class="section">
                <h2>Portfolio Summary</h2>
                <p>Initial Balance: ${results.get('portfolio_summary', {}).get('initial_balance', 0):,.2f}</p>
                <p>Final Equity: ${results.get('portfolio_summary', {}).get('total_equity', 0):,.2f}</p>
                <p>Total Trades: {results.get('additional_metrics', {}).get('total_trades', 0)}</p>
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_file}")
