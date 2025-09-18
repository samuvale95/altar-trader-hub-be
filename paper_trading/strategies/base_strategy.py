"""
Base Strategy Class for Trading Strategies
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, name: str, parameters: Dict = None):
        self.name = name
        self.parameters = parameters or {}
        self.is_active = False
        self.positions = {}  # Track current positions
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on the strategy logic.
        
        Args:
            data: OHLCV data with technical indicators
            
        Returns:
            DataFrame with signals (1 for buy, -1 for sell, 0 for hold)
        """
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict:
        """Get strategy parameters."""
        pass
    
    def set_parameters(self, parameters: Dict):
        """Set strategy parameters."""
        self.parameters.update(parameters)
        logger.info(f"Updated parameters for {self.name}: {self.parameters}")
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate that data has required columns."""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        if data.empty:
            logger.error("Data is empty")
            return False
            
        return True
    
    def calculate_position_size(
        self, 
        current_price: float, 
        portfolio_value: float,
        risk_per_trade: float = 0.02
    ) -> float:
        """
        Calculate position size based on risk management.
        
        Args:
            current_price: Current price of the asset
            portfolio_value: Total portfolio value
            risk_per_trade: Risk per trade as percentage of portfolio
            
        Returns:
            Position size in units
        """
        risk_amount = portfolio_value * risk_per_trade
        position_size = risk_amount / current_price
        return position_size
    
    def get_signal_strength(self, signal: int, data: pd.DataFrame, index: int) -> float:
        """
        Calculate signal strength (0-1) based on various factors.
        
        Args:
            signal: Signal value (1, -1, or 0)
            data: OHLCV data
            index: Current index
            
        Returns:
            Signal strength between 0 and 1
        """
        if signal == 0:
            return 0.0
        
        # Base strength
        strength = 0.5
        
        # Volume confirmation
        if 'volume' in data.columns and 'volume_sma' in data.columns:
            volume_ratio = data['volume'].iloc[index] / data['volume_sma'].iloc[index]
            if volume_ratio > 1.5:  # High volume
                strength += 0.2
            elif volume_ratio < 0.5:  # Low volume
                strength -= 0.1
        
        # Price momentum
        if index > 0:
            price_change = (data['close'].iloc[index] - data['close'].iloc[index-1]) / data['close'].iloc[index-1]
            if abs(price_change) > 0.02:  # Significant price change
                strength += 0.1
        
        # Ensure strength is between 0 and 1
        return max(0.0, min(1.0, strength))
    
    def log_signal(self, timestamp: datetime, symbol: str, signal: int, reason: str, strength: float = 0.0):
        """Log trading signal."""
        signal_text = "BUY" if signal == 1 else "SELL" if signal == -1 else "HOLD"
        logger.info(f"{self.name} - {timestamp} - {symbol}: {signal_text} (strength: {strength:.2f}) - {reason}")
    
    def get_strategy_info(self) -> Dict:
        """Get strategy information."""
        return {
            'name': self.name,
            'parameters': self.parameters,
            'is_active': self.is_active
        }
