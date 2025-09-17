"""
Technical indicators calculations.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, pd.Series]:
    """Calculate MACD (Moving Average Convergence Divergence)."""
    ema_fast = prices.ewm(span=fast_period).mean()
    ema_slow = prices.ewm(span=slow_period).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return {
        'upper': upper_band,
        'middle': sma,
        'lower': lower_band
    }


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average (SMA)."""
    return prices.rolling(window=period).mean()


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average (EMA)."""
    return prices.ewm(span=period).mean()


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                        k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
    """Calculate Stochastic Oscillator."""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_period).mean()
    
    return {
        'k': k_percent,
        'd': d_percent
    }


def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Williams %R."""
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    
    williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
    
    return williams_r


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = true_range.rolling(window=period).mean()
    
    return atr


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index (ADX)."""
    # Calculate True Range
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    
    # Calculate Directional Movement
    high_diff = high.diff()
    low_diff = -low.diff()
    
    plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
    minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
    
    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)
    
    # Calculate smoothed values
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / true_range.rolling(window=period).mean())
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / true_range.rolling(window=period).mean())
    
    # Calculate ADX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx


def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Commodity Channel Index (CCI)."""
    typical_price = (high + low + close) / 3
    sma_tp = typical_price.rolling(window=period).mean()
    mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
    
    cci = (typical_price - sma_tp) / (0.015 * mad)
    
    return cci


def calculate_momentum(prices: pd.Series, period: int = 10) -> pd.Series:
    """Calculate Momentum."""
    return prices / prices.shift(period) - 1


def calculate_rate_of_change(prices: pd.Series, period: int = 10) -> pd.Series:
    """Calculate Rate of Change (ROC)."""
    return (prices - prices.shift(period)) / prices.shift(period) * 100


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate On-Balance Volume (OBV)."""
    obv = np.where(close > close.shift(), volume, 
                  np.where(close < close.shift(), -volume, 0)).cumsum()
    
    return pd.Series(obv, index=close.index)


def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate Volume Weighted Average Price (VWAP)."""
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    
    return vwap


def calculate_ichimoku(high: pd.Series, low: pd.Series, close: pd.Series, 
                      conversion_period: int = 9, base_period: int = 26, 
                      leading_span_b_period: int = 52, displacement: int = 26) -> Dict[str, pd.Series]:
    """Calculate Ichimoku Cloud indicators."""
    # Conversion Line (Tenkan-sen)
    conversion_line = (high.rolling(window=conversion_period).max() + 
                      low.rolling(window=conversion_period).min()) / 2
    
    # Base Line (Kijun-sen)
    base_line = (high.rolling(window=base_period).max() + 
                low.rolling(window=base_period).min()) / 2
    
    # Leading Span A (Senkou Span A)
    leading_span_a = ((conversion_line + base_line) / 2).shift(displacement)
    
    # Leading Span B (Senkou Span B)
    leading_span_b = ((high.rolling(window=leading_span_b_period).max() + 
                      low.rolling(window=leading_span_b_period).min()) / 2).shift(displacement)
    
    # Lagging Span (Chikou Span)
    lagging_span = close.shift(-displacement)
    
    return {
        'conversion_line': conversion_line,
        'base_line': base_line,
        'leading_span_a': leading_span_a,
        'leading_span_b': leading_span_b,
        'lagging_span': lagging_span
    }


def calculate_fibonacci_retracement(high: pd.Series, low: pd.Series) -> Dict[str, pd.Series]:
    """Calculate Fibonacci retracement levels."""
    price_range = high - low
    
    return {
        'level_0': high,
        'level_236': high - (price_range * 0.236),
        'level_382': high - (price_range * 0.382),
        'level_500': high - (price_range * 0.500),
        'level_618': high - (price_range * 0.618),
        'level_786': high - (price_range * 0.786),
        'level_100': low
    }


def calculate_support_resistance(prices: pd.Series, window: int = 20, threshold: float = 0.02) -> Dict[str, List[float]]:
    """Calculate support and resistance levels."""
    # Find local maxima and minima
    local_maxima = prices.rolling(window=window, center=True).max() == prices
    local_minima = prices.rolling(window=window, center=True).min() == prices
    
    # Get support and resistance levels
    resistance_levels = prices[local_maxima].tolist()
    support_levels = prices[local_minima].tolist()
    
    # Filter levels by threshold
    resistance_levels = [level for level in resistance_levels if not pd.isna(level)]
    support_levels = [level for level in support_levels if not pd.isna(level)]
    
    return {
        'resistance': resistance_levels,
        'support': support_levels
    }
