"""
Range Trading Strategy
"""

import pandas as pd
import numpy as np
from typing import Dict
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)


class RangeTradingStrategy(BaseStrategy):
    """Range trading strategy - buy at support, sell at resistance."""
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'lookback_period': 20,  # Period to identify support/resistance
            'support_threshold': 0.02,  # 2% below recent low
            'resistance_threshold': 0.02,  # 2% above recent high
            'min_range_size': 0.05,  # Minimum 5% range size
            'max_range_age': 50,  # Maximum periods to hold range
            'use_volume_confirmation': True,
            'use_rsi_filter': True,  # Use RSI to filter signals
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__("Range_Trading", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate range trading signals."""
        if not self.validate_data(data):
            return pd.DataFrame()
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['reason'] = ''
        signals['strength'] = 0.0
        
        lookback = self.parameters['lookback_period']
        support_thresh = self.parameters['support_threshold']
        resistance_thresh = self.parameters['resistance_threshold']
        min_range = self.parameters['min_range_size']
        
        # Calculate RSI if needed for filtering
        if self.parameters['use_rsi_filter'] and 'rsi' not in data.columns:
            data = self._calculate_rsi(data)
        
        # Generate signals
        for i in range(lookback, len(data)):
            current_price = data['close'].iloc[i]
            high_prices = data['high'].iloc[i-lookback:i+1]
            low_prices = data['low'].iloc[i-lookback:i+1]
            
            # Find support and resistance levels
            support_level = low_prices.min()
            resistance_level = high_prices.max()
            range_size = (resistance_level - support_level) / support_level
            
            signal = 0
            reason = ''
            strength = 0.0
            
            # Check if we have a valid range
            if range_size >= min_range:
                # Buy signal: price near support
                if current_price <= support_level * (1 + support_thresh):
                    if not self.parameters['use_rsi_filter'] or data['rsi'].iloc[i] <= self.parameters['rsi_oversold']:
                        signal = 1
                        reason = f"Range support buy: {current_price:.2f} near {support_level:.2f}"
                        strength = self._calculate_support_strength(current_price, support_level, range_size)
                
                # Sell signal: price near resistance
                elif current_price >= resistance_level * (1 - resistance_thresh):
                    if not self.parameters['use_rsi_filter'] or data['rsi'].iloc[i] >= self.parameters['rsi_overbought']:
                        signal = -1
                        reason = f"Range resistance sell: {current_price:.2f} near {resistance_level:.2f}"
                        strength = self._calculate_resistance_strength(current_price, resistance_level, range_size)
            
            signals.iloc[i, signals.columns.get_loc('signal')] = signal
            signals.iloc[i, signals.columns.get_loc('reason')] = reason
            signals.iloc[i, signals.columns.get_loc('strength')] = strength
        
        # Apply volume confirmation if enabled
        if self.parameters['use_volume_confirmation'] and 'volume_ratio' in data.columns:
            signals = self._apply_volume_confirmation(signals, data)
        
        return signals
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate RSI indicator."""
        data = data.copy()
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        return data
    
    def _calculate_support_strength(self, price: float, support: float, range_size: float) -> float:
        """Calculate signal strength for support level."""
        # Closer to support = stronger signal
        distance = (price - support) / support
        strength = max(0.0, 1.0 - (distance / self.parameters['support_threshold']))
        
        # Larger range = stronger signal
        range_factor = min(1.0, range_size / 0.1)  # Normalize to 10% range
        
        return min(1.0, strength * range_factor)
    
    def _calculate_resistance_strength(self, price: float, resistance: float, range_size: float) -> float:
        """Calculate signal strength for resistance level."""
        # Closer to resistance = stronger signal
        distance = (resistance - price) / resistance
        strength = max(0.0, 1.0 - (distance / self.parameters['resistance_threshold']))
        
        # Larger range = stronger signal
        range_factor = min(1.0, range_size / 0.1)  # Normalize to 10% range
        
        return min(1.0, strength * range_factor)
    
    def _apply_volume_confirmation(self, signals: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
        """Apply volume confirmation to signals."""
        volume_threshold = 1.1  # Require 10% above average volume
        
        for i in range(len(signals)):
            if signals['signal'].iloc[i] != 0:
                if 'volume_ratio' in data.columns:
                    volume_ratio = data['volume_ratio'].iloc[i]
                    if volume_ratio < volume_threshold:
                        # Reduce signal strength if volume is low
                        signals.iloc[i, signals.columns.get_loc('strength')] *= 0.8
                        signals.iloc[i, signals.columns.get_loc('reason')] += f" (low volume: {volume_ratio:.2f})"
        
        return signals
    
    def get_parameters(self) -> Dict:
        """Get range trading strategy parameters."""
        return self.parameters.copy()
