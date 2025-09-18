"""
Bollinger Bands Trading Strategy
"""

import pandas as pd
import numpy as np
from typing import Dict
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands trading strategy."""
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'period': 20,  # Bollinger Bands period
            'std_dev': 2.0,  # Standard deviation multiplier
            'use_squeeze': True,  # Use Bollinger Bands squeeze
            'squeeze_threshold': 0.1,  # Squeeze threshold
            'use_mean_reversion': True,  # Use mean reversion signals
            'use_breakout': True,  # Use breakout signals
            'volume_confirmation': True
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__("Bollinger_Bands", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate Bollinger Bands signals."""
        if not self.validate_data(data):
            return pd.DataFrame()
        
        # Calculate Bollinger Bands if not present
        if 'bb_upper' not in data.columns:
            data = self._calculate_bollinger_bands(data)
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['reason'] = ''
        signals['strength'] = 0.0
        
        period = self.parameters['period']
        std_dev = self.parameters['std_dev']
        squeeze_threshold = self.parameters['squeeze_threshold']
        
        # Generate signals
        for i in range(period, len(data)):
            current_price = data['close'].iloc[i]
            prev_price = data['close'].iloc[i-1]
            upper_band = data['bb_upper'].iloc[i]
            lower_band = data['bb_lower'].iloc[i]
            middle_band = data['bb_middle'].iloc[i]
            bb_width = data['bb_width'].iloc[i]
            
            signal = 0
            reason = ''
            strength = 0.0
            
            # Mean reversion signals
            if self.parameters['use_mean_reversion']:
                # Buy when price touches lower band and bounces
                if (prev_price <= lower_band and current_price > lower_band):
                    signal = 1
                    reason = f"BB mean reversion buy: price bounced from lower band"
                    strength = self._calculate_mean_reversion_strength(current_price, lower_band, middle_band)
                
                # Sell when price touches upper band and rejects
                elif (prev_price >= upper_band and current_price < upper_band):
                    signal = -1
                    reason = f"BB mean reversion sell: price rejected from upper band"
                    strength = self._calculate_mean_reversion_strength(current_price, upper_band, middle_band)
            
            # Breakout signals
            if self.parameters['use_breakout'] and signal == 0:
                # Bullish breakout: price breaks above upper band
                if (prev_price <= upper_band and current_price > upper_band):
                    signal = 1
                    reason = f"BB bullish breakout: price above upper band"
                    strength = self._calculate_breakout_strength(current_price, upper_band, bb_width)
                
                # Bearish breakout: price breaks below lower band
                elif (prev_price >= lower_band and current_price < lower_band):
                    signal = -1
                    reason = f"BB bearish breakout: price below lower band"
                    strength = self._calculate_breakout_strength(current_price, lower_band, bb_width)
            
            # Squeeze signals (low volatility)
            if self.parameters['use_squeeze'] and signal == 0:
                if bb_width < squeeze_threshold:
                    # Look for expansion after squeeze
                    if i > 0 and data['bb_width'].iloc[i-1] >= squeeze_threshold:
                        # Determine direction based on price position relative to middle band
                        if current_price > middle_band:
                            signal = 1
                            reason = f"BB squeeze expansion bullish: {bb_width:.4f}"
                            strength = 0.6
                        else:
                            signal = -1
                            reason = f"BB squeeze expansion bearish: {bb_width:.4f}"
                            strength = 0.6
            
            signals.iloc[i, signals.columns.get_loc('signal')] = signal
            signals.iloc[i, signals.columns.get_loc('reason')] = reason
            signals.iloc[i, signals.columns.get_loc('strength')] = strength
        
        # Apply volume confirmation if enabled
        if self.parameters['volume_confirmation'] and 'volume_ratio' in data.columns:
            signals = self._apply_volume_confirmation(signals, data)
        
        return signals
    
    def _calculate_bollinger_bands(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands."""
        data = data.copy()
        
        period = self.parameters['period']
        std_dev = self.parameters['std_dev']
        
        # Middle band (SMA)
        data['bb_middle'] = data['close'].rolling(window=period).mean()
        
        # Standard deviation
        bb_std = data['close'].rolling(window=period).std()
        
        # Upper and lower bands
        data['bb_upper'] = data['bb_middle'] + (bb_std * std_dev)
        data['bb_lower'] = data['bb_middle'] - (bb_std * std_dev)
        
        # Band width (volatility measure)
        data['bb_width'] = (data['bb_upper'] - data['bb_lower']) / data['bb_middle']
        
        # Band position (where price is relative to bands)
        data['bb_position'] = (data['close'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
        
        return data
    
    def _calculate_mean_reversion_strength(self, price: float, band: float, middle: float) -> float:
        """Calculate signal strength for mean reversion signals."""
        # Strength based on how far price was from the band
        distance = abs(price - band) / middle
        strength = min(1.0, distance * 10)  # Scale factor
        return strength
    
    def _calculate_breakout_strength(self, price: float, band: float, bb_width: float) -> float:
        """Calculate signal strength for breakout signals."""
        # Strength based on breakout distance and band width
        breakout_distance = abs(price - band) / band
        volatility_factor = min(1.0, bb_width * 10)  # Higher volatility = stronger signal
        strength = min(1.0, breakout_distance * volatility_factor * 5)
        return strength
    
    def _apply_volume_confirmation(self, signals: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
        """Apply volume confirmation to signals."""
        volume_threshold = 1.2  # Require 20% above average volume
        
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
        """Get Bollinger Bands strategy parameters."""
        return self.parameters.copy()
