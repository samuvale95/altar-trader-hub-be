"""
Data Feed Module for Historical Crypto Data
"""

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DataFeed:
    """Data feed for historical crypto data from various sources."""
    
    def __init__(self):
        self.binance_base_url = "https://api.binance.com/api/v3"
        self.yahoo_base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        
    def get_binance_data(
        self, 
        symbol: str, 
        interval: str, 
        start_date: str, 
        end_date: str = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Get historical data from Binance API.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Time interval (1h, 4h, 1d, etc.)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
            limit: Maximum number of records (max 1000)
        """
        try:
            # Convert interval to Binance format
            interval_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
                '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
            }
            
            if interval not in interval_map:
                raise ValueError(f"Unsupported interval: {interval}")
                
            binance_interval = interval_map[interval]
            
            # Convert dates to timestamps
            start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
            end_ts = int(pd.Timestamp(end_date).timestamp() * 1000) if end_date else None
            
            url = f"{self.binance_base_url}/klines"
            params = {
                'symbol': symbol,
                'interval': binance_interval,
                'startTime': start_ts,
                'limit': limit
            }
            
            if end_ts:
                params['endTime'] = end_ts
                
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert to proper types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            # Keep only OHLCV data
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            logger.info(f"Downloaded {len(df)} records for {symbol} {interval}")
            return df
            
        except Exception as e:
            logger.error(f"Error downloading data from Binance: {e}")
            raise
    
    def get_yahoo_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str = None
    ) -> pd.DataFrame:
        """
        Get historical data from Yahoo Finance.
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USD')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        try:
            # Convert dates to timestamps
            start_ts = int(pd.Timestamp(start_date).timestamp())
            end_ts = int(pd.Timestamp(end_date).timestamp()) if end_date else int(time.time())
            
            url = f"{self.yahoo_base_url}/{symbol}"
            params = {
                'period1': start_ts,
                'period2': end_ts,
                'interval': '1d',
                'includePrePost': 'true',
                'events': 'div%2Csplit'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' not in data or not data['chart']['result']:
                raise ValueError(f"No data found for symbol: {symbol}")
                
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]
            
            # Create DataFrame
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(timestamps, unit='s'),
                'open': quotes['open'],
                'high': quotes['high'],
                'low': quotes['low'],
                'close': quotes['close'],
                'volume': quotes['volume']
            })
            
            # Remove NaN values
            df = df.dropna()
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            # Keep only OHLCV data
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            logger.info(f"Downloaded {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error downloading data from Yahoo Finance: {e}")
            raise
    
    def get_data(
        self, 
        symbol: str, 
        interval: str = '1d',
        start_date: str = None,
        end_date: str = None,
        source: str = 'binance'
    ) -> pd.DataFrame:
        """
        Get historical data from specified source.
        
        Args:
            symbol: Trading pair
            interval: Time interval
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            source: Data source ('binance' or 'yahoo')
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        if source.lower() == 'binance':
            return self.get_binance_data(symbol, interval, start_date, end_date)
        elif source.lower() == 'yahoo':
            return self.get_yahoo_data(symbol, start_date, end_date)
        else:
            raise ValueError(f"Unsupported data source: {source}")
    
    def save_data(self, df: pd.DataFrame, filename: str):
        """Save data to CSV file."""
        df.to_csv(filename)
        logger.info(f"Data saved to {filename}")
    
    def load_data(self, filename: str) -> pd.DataFrame:
        """Load data from CSV file."""
        df = pd.read_csv(filename, index_col=0, parse_dates=True)
        logger.info(f"Data loaded from {filename}")
        return df


class DataProcessor:
    """Data processing utilities for technical analysis."""
    
    @staticmethod
    def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add common technical indicators to the dataframe."""
        df = df.copy()
        
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        return df
    
    @staticmethod
    def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate various return metrics."""
        df = df.copy()
        
        # Price returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Cumulative returns
        df['cumulative_returns'] = (1 + df['returns']).cumprod() - 1
        
        return df
