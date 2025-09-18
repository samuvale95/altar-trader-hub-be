"""
Dollar Cost Averaging (DCA) Strategy
"""

import pandas as pd
import numpy as np
from typing import Dict
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)


class DCAStrategy(BaseStrategy):
    """Dollar Cost Averaging Strategy - Buy fixed amount at regular intervals."""
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'investment_amount': 100.0,  # Amount to invest each period
            'frequency': 7,  # Days between investments
            'max_investments': 52,  # Maximum number of investments
            'start_date': None,  # Start date for DCA
            'end_date': None  # End date for DCA
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__("DCA", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate DCA signals."""
        if not self.validate_data(data):
            return pd.DataFrame()
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['reason'] = ''
        signals['strength'] = 0.0
        
        # Calculate investment dates
        investment_dates = self._calculate_investment_dates(data)
        
        for date in investment_dates:
            if date in data.index:
                idx = data.index.get_loc(date)
                signals.loc[date, 'signal'] = 1  # Always buy
                signals.loc[date, 'reason'] = f"DCA investment #{len([d for d in investment_dates if d <= date])}"
                signals.loc[date, 'strength'] = 1.0  # Full strength for DCA
        
        return signals
    
    def _calculate_investment_dates(self, data: pd.DataFrame) -> list:
        """Calculate investment dates based on frequency."""
        start_date = self.parameters.get('start_date')
        end_date = self.parameters.get('end_date')
        frequency = self.parameters['frequency']
        max_investments = self.parameters['max_investments']
        
        if start_date:
            start_date = pd.Timestamp(start_date)
        else:
            start_date = data.index[0]
        
        if end_date:
            end_date = pd.Timestamp(end_date)
        else:
            end_date = data.index[-1]
        
        # Generate investment dates
        investment_dates = []
        current_date = start_date
        investment_count = 0
        
        while current_date <= end_date and investment_count < max_investments:
            if current_date in data.index:
                investment_dates.append(current_date)
                investment_count += 1
            current_date += pd.Timedelta(days=frequency)
        
        return investment_dates
    
    def get_parameters(self) -> Dict:
        """Get DCA parameters."""
        return self.parameters.copy()
    
    def calculate_investment_amount(self, current_price: float) -> float:
        """Calculate how many units to buy with fixed amount."""
        investment_amount = self.parameters['investment_amount']
        return investment_amount / current_price
