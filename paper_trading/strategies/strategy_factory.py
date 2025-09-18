"""
Strategy Factory for creating trading strategies
"""

from typing import Dict, Type
from .base_strategy import BaseStrategy
from .dca_strategy import DCAStrategy
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .ma_crossover_strategy import MACrossoverStrategy
from .bollinger_bands_strategy import BollingerBandsStrategy
from .range_trading_strategy import RangeTradingStrategy
from .grid_trading_strategy import GridTradingStrategy
from .fear_greed_strategy import FearGreedStrategy
import logging

logger = logging.getLogger(__name__)


class StrategyFactory:
    """Factory class for creating trading strategies."""
    
    _strategies = {
        'dca': DCAStrategy,
        'rsi': RSIStrategy,
        'macd': MACDStrategy,
        'ma_crossover': MACrossoverStrategy,
        'bollinger_bands': BollingerBandsStrategy,
        'range_trading': RangeTradingStrategy,
        'grid_trading': GridTradingStrategy,
        'fear_greed': FearGreedStrategy
    }
    
    @classmethod
    def create_strategy(cls, strategy_name: str, parameters: Dict = None) -> BaseStrategy:
        """
        Create a trading strategy instance.
        
        Args:
            strategy_name: Name of the strategy
            parameters: Strategy parameters
            
        Returns:
            Strategy instance
        """
        strategy_name = strategy_name.lower()
        
        if strategy_name not in cls._strategies:
            available = ', '.join(cls._strategies.keys())
            raise ValueError(f"Unknown strategy: {strategy_name}. Available strategies: {available}")
        
        strategy_class = cls._strategies[strategy_name]
        strategy = strategy_class(parameters)
        
        logger.info(f"Created strategy: {strategy_name} with parameters: {parameters}")
        return strategy
    
    @classmethod
    def get_available_strategies(cls) -> list:
        """Get list of available strategy names."""
        return list(cls._strategies.keys())
    
    @classmethod
    def get_strategy_info(cls, strategy_name: str) -> Dict:
        """Get information about a strategy."""
        strategy_name = strategy_name.lower()
        
        if strategy_name not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        strategy_class = cls._strategies[strategy_name]
        
        # Create a temporary instance to get default parameters
        temp_strategy = strategy_class()
        
        return {
            'name': strategy_name,
            'class': strategy_class.__name__,
            'description': strategy_class.__doc__ or "No description available",
            'default_parameters': temp_strategy.get_parameters()
        }
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[BaseStrategy]):
        """
        Register a new strategy.
        
        Args:
            name: Strategy name
            strategy_class: Strategy class
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError("Strategy class must inherit from BaseStrategy")
        
        cls._strategies[name.lower()] = strategy_class
        logger.info(f"Registered new strategy: {name}")
    
    @classmethod
    def get_all_strategies_info(cls) -> Dict:
        """Get information about all available strategies."""
        info = {}
        for name in cls._strategies.keys():
            try:
                info[name] = cls.get_strategy_info(name)
            except Exception as e:
                logger.error(f"Error getting info for strategy {name}: {e}")
                info[name] = {'error': str(e)}
        
        return info
