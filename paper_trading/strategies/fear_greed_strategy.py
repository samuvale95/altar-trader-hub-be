"""
Fear & Greed Index Trading Strategy
"""

import pandas as pd
import numpy as np
import requests
from typing import Dict
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)


class FearGreedStrategy(BaseStrategy):
    """Fear & Greed Index trading strategy."""
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'fear_threshold': 25,  # Buy when fear index below this
            'greed_threshold': 75,  # Sell when greed index above this
            'neutral_zone': 45,  # Exit when index returns to neutral
            'use_sentiment_momentum': True,  # Use sentiment change for signals
            'momentum_period': 5,  # Period for momentum calculation
            'data_source': 'alternative',  # 'alternative' or 'cnn'
            'update_frequency': 24  # Hours between updates
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__("Fear_Greed", default_params)
        self.last_fear_greed = None
        self.last_update = None
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate Fear & Greed Index signals."""
        if not self.validate_data(data):
            return pd.DataFrame()
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['reason'] = ''
        signals['strength'] = 0.0
        
        # Get Fear & Greed Index data
        fear_greed_data = self._get_fear_greed_data()
        
        if fear_greed_data is None:
            logger.warning("Could not fetch Fear & Greed Index data")
            return signals
        
        # Generate signals
        for i in range(len(data)):
            current_fear_greed = fear_greed_data.get('value', 50)  # Default to neutral
            current_timestamp = data.index[i]
            
            signal = 0
            reason = ''
            strength = 0.0
            
            # Buy signal: Extreme fear
            if current_fear_greed <= self.parameters['fear_threshold']:
                signal = 1
                reason = f"Extreme fear: {current_fear_greed}"
                strength = self._calculate_fear_strength(current_fear_greed)
            
            # Sell signal: Extreme greed
            elif current_fear_greed >= self.parameters['greed_threshold']:
                signal = -1
                reason = f"Extreme greed: {current_fear_greed}"
                strength = self._calculate_greed_strength(current_fear_greed)
            
            # Exit signal: Return to neutral
            elif (self.last_fear_greed is not None and 
                  abs(self.last_fear_greed - self.parameters['neutral_zone']) > 
                  abs(current_fear_greed - self.parameters['neutral_zone'])):
                signal = 0
                reason = f"Returning to neutral: {current_fear_greed}"
                strength = 0.5
            
            # Sentiment momentum signals
            if self.parameters['use_sentiment_momentum'] and signal == 0:
                momentum_signal = self._calculate_sentiment_momentum(fear_greed_data, i)
                if momentum_signal != 0:
                    signal = momentum_signal
                    reason = f"Sentiment momentum: {current_fear_greed}"
                    strength = 0.6
            
            signals.iloc[i, signals.columns.get_loc('signal')] = signal
            signals.iloc[i, signals.columns.get_loc('reason')] = reason
            signals.iloc[i, signals.columns.get_loc('strength')] = strength
            
            self.last_fear_greed = current_fear_greed
        
        return signals
    
    def _get_fear_greed_data(self) -> Dict:
        """Fetch Fear & Greed Index data."""
        try:
            if self.parameters['data_source'] == 'alternative':
                # Alternative.me Fear & Greed Index
                url = "https://api.alternative.me/fng/"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    return {
                        'value': int(data['data'][0]['value']),
                        'classification': data['data'][0]['value_classification'],
                        'timestamp': data['data'][0]['timestamp']
                    }
            
            elif self.parameters['data_source'] == 'cnn':
                # CNN Fear & Greed Index (simplified - would need web scraping)
                # For now, return a mock value
                return {
                    'value': 50,  # Mock neutral value
                    'classification': 'Neutral',
                    'timestamp': str(int(pd.Timestamp.now().timestamp()))
                }
            
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {e}")
        
        return None
    
    def _calculate_fear_strength(self, fear_greed_value: int) -> float:
        """Calculate signal strength for fear signals."""
        # Lower fear index = stronger buy signal
        strength = (self.parameters['fear_threshold'] - fear_greed_value) / self.parameters['fear_threshold']
        return min(1.0, max(0.0, strength))
    
    def _calculate_greed_strength(self, fear_greed_value: int) -> float:
        """Calculate signal strength for greed signals."""
        # Higher greed index = stronger sell signal
        strength = (fear_greed_value - self.parameters['greed_threshold']) / (100 - self.parameters['greed_threshold'])
        return min(1.0, max(0.0, strength))
    
    def _calculate_sentiment_momentum(self, fear_greed_data: Dict, index: int) -> int:
        """Calculate sentiment momentum signals."""
        # This is a simplified implementation
        # In practice, you would need historical Fear & Greed data
        current_value = fear_greed_data.get('value', 50)
        
        # Simple momentum based on current value
        if current_value < 30:  # Strong fear momentum
            return 1
        elif current_value > 70:  # Strong greed momentum
            return -1
        
        return 0
    
    def get_parameters(self) -> Dict:
        """Get Fear & Greed strategy parameters."""
        return self.parameters.copy()
    
    def get_current_fear_greed(self) -> Dict:
        """Get current Fear & Greed Index value."""
        return self._get_fear_greed_data()
