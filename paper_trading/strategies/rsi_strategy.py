"""
RSI (Relative Strength Index) Trading Strategy
"""

import pandas as pd
import numpy as np
from typing import Dict
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)


class RSIStrategy(BaseStrategy):
    """RSI-based trading strategy."""
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'rsi_exit_threshold': 50,  # Exit when RSI crosses this level
            'min_holding_period': 1,  # Minimum periods to hold position
            'use_divergence': False,  # Use RSI divergence signals
            'volume_confirmation': True  # Require volume confirmation
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__("RSI", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate RSI-based signals."""
        if not self.validate_data(data):
            return pd.DataFrame()
        
        # Calculate RSI if not present
        if 'rsi' not in data.columns:
            data = self._calculate_rsi(data)
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['reason'] = ''
        signals['strength'] = 0.0
        
        rsi_period = self.parameters['rsi_period']
        oversold = self.parameters['oversold_threshold']
        overbought = self.parameters['overbought_threshold']
        exit_threshold = self.parameters['rsi_exit_threshold']
        
        # Generate signals
        for i in range(rsi_period, len(data)):
            current_rsi = data['rsi'].iloc[i]
            prev_rsi = data['rsi'].iloc[i-1]
            
            # Buy signal: RSI crosses above oversold level
            if (prev_rsi <= oversold and current_rsi > oversold):
                signals.iloc[i, signals.columns.get_loc('signal')] = 1
                signals.iloc[i, signals.columns.get_loc('reason')] = f"RSI oversold bounce: {current_rsi:.1f}"
                strength = self._calculate_rsi_strength(current_rsi, oversold, overbought, 'buy')
                signals.iloc[i, signals.columns.get_loc('strength')] = strength
                
            # Sell signal: RSI crosses below overbought level
            elif (prev_rsi >= overbought and current_rsi < overbought):
                signals.iloc[i, signals.columns.get_loc('signal')] = -1
                signals.iloc[i, signals.columns.get_loc('reason')] = f"RSI overbought rejection: {current_rsi:.1f}"
                strength = self._calculate_rsi_strength(current_rsi, oversold, overbought, 'sell')
                signals.iloc[i, signals.columns.get_loc('strength')] = strength
                
            # Exit signal: RSI crosses back to neutral zone
            elif (prev_rsi < exit_threshold and current_rsi >= exit_threshold) or \
                 (prev_rsi > exit_threshold and current_rsi <= exit_threshold):
                signals.iloc[i, signals.columns.get_loc('signal')] = 0
                signals.iloc[i, signals.columns.get_loc('reason')] = f"RSI neutral zone: {current_rsi:.1f}"
                signals.iloc[i, signals.columns.get_loc('strength')] = 0.5
        
        # Apply volume confirmation if enabled
        if self.parameters['volume_confirmation'] and 'volume_ratio' in data.columns:
            signals = self._apply_volume_confirmation(signals, data)
        
        return signals
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = None) -> pd.DataFrame:
        """Calculate RSI indicator."""
        if period is None:
            period = self.parameters['rsi_period']
        
        data = data.copy()
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        return data
    
    def _calculate_rsi_strength(self, rsi: float, oversold: float, overbought: float, signal_type: str) -> float:
        """Calculate signal strength based on RSI value."""
        if signal_type == 'buy':
            # Stronger signal when RSI is further below oversold
            strength = max(0.0, (oversold - rsi) / oversold)
        else:  # sell
            # Stronger signal when RSI is further above overbought
            strength = max(0.0, (rsi - overbought) / (100 - overbought))
        
        return min(1.0, strength)
    
    def _apply_volume_confirmation(self, signals: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
        """Apply volume confirmation to signals."""
        volume_threshold = 1.2  # Require 20% above average volume
        
        for i in range(len(signals)):
            if signals['signal'].iloc[i] != 0:
                if 'volume_ratio' in data.columns:
                    volume_ratio = data['volume_ratio'].iloc[i]
                    if volume_ratio < volume_threshold:
                        # Reduce signal strength if volume is low
                        signals.iloc[i, signals.columns.get_loc('strength')] *= 0.5
                        signals.iloc[i, signals.columns.get_loc('reason')] += f" (low volume: {volume_ratio:.2f})"
        
        return signals
    
    def get_parameters(self) -> Dict:
        """Get RSI strategy parameters."""
        return self.parameters.copy()
