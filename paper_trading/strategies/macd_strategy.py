"""
MACD (Moving Average Convergence Divergence) Trading Strategy
"""

import pandas as pd
import numpy as np
from typing import Dict
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)


class MACDStrategy(BaseStrategy):
    """MACD-based trading strategy."""
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'use_histogram': True,  # Use MACD histogram for signals
            'use_crossover': True,  # Use MACD line crossover for signals
            'min_histogram_change': 0.001,  # Minimum histogram change for signal
            'volume_confirmation': True
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__("MACD", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate MACD-based signals."""
        if not self.validate_data(data):
            return pd.DataFrame()
        
        # Calculate MACD if not present
        if 'macd' not in data.columns or 'macd_signal' not in data.columns:
            data = self._calculate_macd(data)
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['reason'] = ''
        signals['strength'] = 0.0
        
        fast_period = self.parameters['fast_period']
        slow_period = self.parameters['slow_period']
        signal_period = self.parameters['signal_period']
        min_histogram_change = self.parameters['min_histogram_change']
        
        # Generate signals
        for i in range(max(fast_period, slow_period, signal_period), len(data)):
            current_macd = data['macd'].iloc[i]
            prev_macd = data['macd'].iloc[i-1]
            current_signal = data['macd_signal'].iloc[i]
            prev_signal = data['macd_signal'].iloc[i-1]
            current_histogram = data['macd_histogram'].iloc[i]
            prev_histogram = data['macd_histogram'].iloc[i-1]
            
            signal = 0
            reason = ''
            strength = 0.0
            
            # MACD line crossover signals
            if self.parameters['use_crossover']:
                # Bullish crossover: MACD crosses above signal line
                if (prev_macd <= prev_signal and current_macd > current_signal):
                    signal = 1
                    reason = f"MACD bullish crossover: {current_macd:.4f} > {current_signal:.4f}"
                    strength = self._calculate_crossover_strength(current_macd, current_signal, 'bullish')
                
                # Bearish crossover: MACD crosses below signal line
                elif (prev_macd >= prev_signal and current_macd < current_signal):
                    signal = -1
                    reason = f"MACD bearish crossover: {current_macd:.4f} < {current_signal:.4f}"
                    strength = self._calculate_crossover_strength(current_macd, current_signal, 'bearish')
            
            # MACD histogram signals
            if self.parameters['use_histogram'] and signal == 0:
                histogram_change = current_histogram - prev_histogram
                
                # Bullish histogram: histogram turns positive
                if (prev_histogram <= 0 and current_histogram > 0 and 
                    abs(histogram_change) >= min_histogram_change):
                    signal = 1
                    reason = f"MACD histogram bullish: {current_histogram:.4f}"
                    strength = min(1.0, abs(current_histogram) * 1000)  # Scale histogram value
                
                # Bearish histogram: histogram turns negative
                elif (prev_histogram >= 0 and current_histogram < 0 and 
                      abs(histogram_change) >= min_histogram_change):
                    signal = -1
                    reason = f"MACD histogram bearish: {current_histogram:.4f}"
                    strength = min(1.0, abs(current_histogram) * 1000)  # Scale histogram value
            
            # Zero line crossover signals
            if signal == 0:
                # MACD crosses above zero line
                if (prev_macd <= 0 and current_macd > 0):
                    signal = 1
                    reason = f"MACD zero line bullish: {current_macd:.4f}"
                    strength = 0.7
                
                # MACD crosses below zero line
                elif (prev_macd >= 0 and current_macd < 0):
                    signal = -1
                    reason = f"MACD zero line bearish: {current_macd:.4f}"
                    strength = 0.7
            
            signals.iloc[i, signals.columns.get_loc('signal')] = signal
            signals.iloc[i, signals.columns.get_loc('reason')] = reason
            signals.iloc[i, signals.columns.get_loc('strength')] = strength
        
        # Apply volume confirmation if enabled
        if self.parameters['volume_confirmation'] and 'volume_ratio' in data.columns:
            signals = self._apply_volume_confirmation(signals, data)
        
        return signals
    
    def _calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD indicator."""
        data = data.copy()
        
        fast_period = self.parameters['fast_period']
        slow_period = self.parameters['slow_period']
        signal_period = self.parameters['signal_period']
        
        # Calculate EMAs
        ema_fast = data['close'].ewm(span=fast_period).mean()
        ema_slow = data['close'].ewm(span=slow_period).mean()
        
        # MACD line
        data['macd'] = ema_fast - ema_slow
        
        # Signal line
        data['macd_signal'] = data['macd'].ewm(span=signal_period).mean()
        
        # Histogram
        data['macd_histogram'] = data['macd'] - data['macd_signal']
        
        return data
    
    def _calculate_crossover_strength(self, macd: float, signal: float, crossover_type: str) -> float:
        """Calculate signal strength based on MACD crossover."""
        difference = abs(macd - signal)
        
        # Normalize the difference (this is a simplified approach)
        # In practice, you might want to use historical data to normalize
        strength = min(1.0, difference * 1000)  # Scale factor
        
        return strength
    
    def _apply_volume_confirmation(self, signals: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
        """Apply volume confirmation to signals."""
        volume_threshold = 1.1  # Require 10% above average volume
        
        for i in range(len(signals)):
            if signals['signal'].iloc[i] != 0:
                if 'volume_ratio' in data.columns:
                    volume_ratio = data['volume_ratio'].iloc[i]
                    if volume_ratio < volume_threshold:
                        # Reduce signal strength if volume is low
                        signals.iloc[i, signals.columns.get_loc('strength')] *= 0.7
                        signals.iloc[i, signals.columns.get_loc('reason')] += f" (low volume: {volume_ratio:.2f})"
        
        return signals
    
    def get_parameters(self) -> Dict:
        """Get MACD strategy parameters."""
        return self.parameters.copy()
