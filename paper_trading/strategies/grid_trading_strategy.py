"""
Grid Trading Strategy
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)


class GridTradingStrategy(BaseStrategy):
    """Grid trading strategy - place buy/sell orders at regular intervals."""
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'grid_size': 0.01,  # 1% grid size
            'grid_levels': 10,  # Number of grid levels
            'base_price': None,  # Base price for grid (if None, use current price)
            'max_position': 1000,  # Maximum position size
            'min_position': 100,  # Minimum position size
            'use_dynamic_grid': True,  # Adjust grid based on volatility
            'volatility_period': 20,  # Period for volatility calculation
            'use_trend_filter': True,  # Only trade in trending markets
            'trend_period': 50  # Period for trend calculation
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__("Grid_Trading", default_params)
        self.grid_levels = []
        self.last_price = None
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate grid trading signals."""
        if not self.validate_data(data):
            return pd.DataFrame()
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['reason'] = ''
        signals['strength'] = 0.0
        
        # Initialize grid if needed
        if not self.grid_levels or self.parameters['use_dynamic_grid']:
            self._update_grid(data.iloc[0]['close'])
        
        # Generate signals
        for i in range(len(data)):
            current_price = data['close'].iloc[i]
            
            # Update grid if using dynamic grid
            if self.parameters['use_dynamic_grid']:
                self._update_dynamic_grid(data, i)
            
            signal = 0
            reason = ''
            strength = 0.0
            
            # Check for grid level crossings
            if self.last_price is not None:
                for level in self.grid_levels:
                    # Buy signal: price crosses above a buy level
                    if (self.last_price <= level['price'] and current_price > level['price'] and 
                        level['type'] == 'buy'):
                        signal = 1
                        reason = f"Grid buy at {level['price']:.2f}"
                        strength = 0.8
                        break
                    
                    # Sell signal: price crosses below a sell level
                    elif (self.last_price >= level['price'] and current_price < level['price'] and 
                          level['type'] == 'sell'):
                        signal = -1
                        reason = f"Grid sell at {level['price']:.2f}"
                        strength = 0.8
                        break
            
            # Apply trend filter if enabled
            if self.parameters['use_trend_filter'] and signal != 0:
                trend = self._calculate_trend(data, i)
                if signal == 1 and trend < 0:  # Don't buy in downtrend
                    signal = 0
                    reason = "Trend filter: downtrend detected"
                elif signal == -1 and trend > 0:  # Don't sell in uptrend
                    signal = 0
                    reason = "Trend filter: uptrend detected"
            
            signals.iloc[i, signals.columns.get_loc('signal')] = signal
            signals.iloc[i, signals.columns.get_loc('reason')] = reason
            signals.iloc[i, signals.columns.get_loc('strength')] = strength
            
            self.last_price = current_price
        
        return signals
    
    def _update_grid(self, base_price: float):
        """Update grid levels based on current price."""
        grid_size = self.parameters['grid_size']
        grid_levels = self.parameters['grid_levels']
        
        self.grid_levels = []
        
        # Create buy levels below current price
        for i in range(1, grid_levels + 1):
            buy_price = base_price * (1 - grid_size * i)
            self.grid_levels.append({
                'price': buy_price,
                'type': 'buy',
                'level': i
            })
        
        # Create sell levels above current price
        for i in range(1, grid_levels + 1):
            sell_price = base_price * (1 + grid_size * i)
            self.grid_levels.append({
                'price': sell_price,
                'type': 'sell',
                'level': i
            })
        
        # Sort by price
        self.grid_levels.sort(key=lambda x: x['price'])
    
    def _update_dynamic_grid(self, data: pd.DataFrame, index: int):
        """Update grid based on volatility."""
        if index < self.parameters['volatility_period']:
            return
        
        # Calculate recent volatility
        recent_prices = data['close'].iloc[index-self.parameters['volatility_period']:index+1]
        returns = recent_prices.pct_change().dropna()
        volatility = returns.std()
        
        # Adjust grid size based on volatility
        base_volatility = 0.02  # 2% base volatility
        volatility_factor = min(2.0, max(0.5, volatility / base_volatility))
        
        current_price = data['close'].iloc[index]
        adjusted_grid_size = self.parameters['grid_size'] * volatility_factor
        
        # Update grid with adjusted size
        self.parameters['grid_size'] = adjusted_grid_size
        self._update_grid(current_price)
    
    def _calculate_trend(self, data: pd.DataFrame, index: int) -> float:
        """Calculate trend direction."""
        trend_period = self.parameters['trend_period']
        
        if index < trend_period:
            return 0
        
        # Simple trend calculation using price change
        start_price = data['close'].iloc[index - trend_period]
        end_price = data['close'].iloc[index]
        
        trend = (end_price - start_price) / start_price
        return trend
    
    def get_grid_levels(self) -> List[Dict]:
        """Get current grid levels."""
        return self.grid_levels.copy()
    
    def get_parameters(self) -> Dict:
        """Get grid trading strategy parameters."""
        return self.parameters.copy()
