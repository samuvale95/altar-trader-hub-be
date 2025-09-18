"""
Moving Average Crossover Trading Strategy
"""

import pandas as pd
import numpy as np
from typing import Dict
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)


class MACrossoverStrategy(BaseStrategy):
    """Moving Average Crossover trading strategy."""
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'fast_period': 10,  # Fast moving average period
            'slow_period': 30,  # Slow moving average period
            'ma_type': 'SMA',  # SMA or EMA
            'use_trend_filter': True,  # Use longer MA as trend filter
            'trend_period': 200,  # Trend filter period
            'min_crossover_gap': 0.001,  # Minimum gap for crossover signal
            'volume_confirmation': True
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__("MA_Crossover", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate MA crossover signals."""
        if not self.validate_data(data):
            return pd.DataFrame()
        
        # Calculate moving averages if not present
        if f"sma_{self.parameters['fast_period']}" not in data.columns:
            data = self._calculate_moving_averages(data)
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['reason'] = ''
        signals['strength'] = 0.0
        
        fast_period = self.parameters['fast_period']
        slow_period = self.parameters['slow_period']
        ma_type = self.parameters['ma_type']
        min_gap = self.parameters['min_crossover_gap']
        
        fast_col = f"{ma_type.lower()}_{fast_period}"
        slow_col = f"{ma_type.lower()}_{slow_period}"
        
        # Generate signals
        for i in range(slow_period, len(data)):
            current_fast = data[fast_col].iloc[i]
            prev_fast = data[fast_col].iloc[i-1]
            current_slow = data[slow_col].iloc[i]
            prev_slow = data[slow_col].iloc[i-1]
            
            signal = 0
            reason = ''
            strength = 0.0
            
            # Check for crossover
            if (prev_fast <= prev_slow and current_fast > current_slow):
                # Bullish crossover
                gap = (current_fast - current_slow) / current_slow
                if gap >= min_gap:
                    signal = 1
                    reason = f"Bullish {ma_type} crossover: {fast_period} > {slow_period}"
                    strength = self._calculate_crossover_strength(gap, 'bullish')
                    
            elif (prev_fast >= prev_slow and current_fast < current_slow):
                # Bearish crossover
                gap = (prev_slow - current_fast) / current_slow
                if gap >= min_gap:
                    signal = -1
                    reason = f"Bearish {ma_type} crossover: {fast_period} < {slow_period}"
                    strength = self._calculate_crossover_strength(gap, 'bearish')
            
            # Apply trend filter if enabled
            if self.parameters['use_trend_filter'] and signal != 0:
                trend_col = f"{ma_type.lower()}_{self.parameters['trend_period']}"
                if trend_col in data.columns:
                    current_price = data['close'].iloc[i]
                    trend_ma = data[trend_col].iloc[i]
                    
                    # Only allow buy signals in uptrend, sell signals in downtrend
                    if signal == 1 and current_price < trend_ma:
                        signal = 0
                        reason = "Trend filter: Price below long-term MA"
                    elif signal == -1 and current_price > trend_ma:
                        signal = 0
                        reason = "Trend filter: Price above long-term MA"
                    else:
                        reason += f" (trend confirmed)"
            
            signals.iloc[i, signals.columns.get_loc('signal')] = signal
            signals.iloc[i, signals.columns.get_loc('reason')] = reason
            signals.iloc[i, signals.columns.get_loc('strength')] = strength
        
        # Apply volume confirmation if enabled
        if self.parameters['volume_confirmation'] and 'volume_ratio' in data.columns:
            signals = self._apply_volume_confirmation(signals, data)
        
        return signals
    
    def _calculate_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages."""
        data = data.copy()
        
        fast_period = self.parameters['fast_period']
        slow_period = self.parameters['slow_period']
        trend_period = self.parameters['trend_period']
        ma_type = self.parameters['ma_type']
        
        if ma_type.upper() == 'SMA':
            data[f'sma_{fast_period}'] = data['close'].rolling(window=fast_period).mean()
            data[f'sma_{slow_period}'] = data['close'].rolling(window=slow_period).mean()
            if self.parameters['use_trend_filter']:
                data[f'sma_{trend_period}'] = data['close'].rolling(window=trend_period).mean()
        else:  # EMA
            data[f'ema_{fast_period}'] = data['close'].ewm(span=fast_period).mean()
            data[f'ema_{slow_period}'] = data['close'].ewm(span=slow_period).mean()
            if self.parameters['use_trend_filter']:
                data[f'ema_{trend_period}'] = data['close'].ewm(span=trend_period).mean()
        
        return data
    
    def _calculate_crossover_strength(self, gap: float, crossover_type: str) -> float:
        """Calculate signal strength based on crossover gap."""
        # Normalize the gap to 0-1 range
        # This is a simplified approach - in practice, you might want to use historical data
        strength = min(1.0, gap * 100)  # Scale factor
        
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
                        signals.iloc[i, signals.columns.get_loc('strength')] *= 0.8
                        signals.iloc[i, signals.columns.get_loc('reason')] += f" (low volume: {volume_ratio:.2f})"
        
        return signals
    
    def get_parameters(self) -> Dict:
        """Get MA crossover strategy parameters."""
        return self.parameters.copy()
