"""
Paper Trading System for Crypto Strategies Simulation
"""

__version__ = "1.0.0"
__author__ = "Altar Trader Hub"

from .core.portfolio import VirtualPortfolio
from .core.data_feed import DataFeed
from .core.backtest_engine import BacktestEngine
from .strategies import StrategyFactory

__all__ = [
    "VirtualPortfolio",
    "DataFeed", 
    "BacktestEngine",
    "StrategyFactory"
]
