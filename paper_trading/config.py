"""
Configuration file for Paper Trading System
"""

# Default configuration
DEFAULT_CONFIG = {
    # Data settings
    'data': {
        'default_symbol': 'BTCUSDT',
        'default_interval': '1d',
        'default_source': 'binance',
        'cache_data': True,
        'cache_dir': 'data_cache'
    },
    
    # Portfolio settings
    'portfolio': {
        'initial_balance': 10000.0,
        'commission_rate': 0.001,
        'base_currency': 'USDT',
        'min_position_size': 0.001
    },
    
    # Strategy settings
    'strategies': {
        'dca': {
            'investment_amount': 100.0,
            'frequency': 7,
            'max_investments': 52
        },
        'rsi': {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'rsi_exit_threshold': 50
        },
        'macd': {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'use_histogram': True,
            'use_crossover': True
        },
        'ma_crossover': {
            'fast_period': 10,
            'slow_period': 30,
            'ma_type': 'SMA',
            'use_trend_filter': True,
            'trend_period': 200
        },
        'bollinger_bands': {
            'period': 20,
            'std_dev': 2.0,
            'use_squeeze': True,
            'use_mean_reversion': True,
            'use_breakout': True
        },
        'range_trading': {
            'lookback_period': 20,
            'support_threshold': 0.02,
            'resistance_threshold': 0.02,
            'min_range_size': 0.05
        },
        'grid_trading': {
            'grid_size': 0.01,
            'grid_levels': 10,
            'use_dynamic_grid': True,
            'volatility_period': 20
        },
        'fear_greed': {
            'fear_threshold': 25,
            'greed_threshold': 75,
            'neutral_zone': 45,
            'data_source': 'alternative'
        }
    },
    
    # Backtesting settings
    'backtest': {
        'default_start_date': '2023-01-01',
        'default_end_date': None,  # Current date
        'risk_per_trade': 0.02,
        'max_trades_per_day': 10
    },
    
    # Reporting settings
    'reporting': {
        'generate_plots': True,
        'generate_html': True,
        'save_trades': True,
        'save_orders': True,
        'save_equity_curve': True
    }
}

# Strategy descriptions
STRATEGY_DESCRIPTIONS = {
    'dca': {
        'name': 'Dollar Cost Averaging',
        'description': 'Invests a fixed amount at regular intervals regardless of price',
        'risk_level': 'Low',
        'best_for': 'Long-term investors, beginners'
    },
    'rsi': {
        'name': 'RSI Trading',
        'description': 'Buys when RSI is oversold, sells when overbought',
        'risk_level': 'Medium',
        'best_for': 'Mean reversion traders'
    },
    'macd': {
        'name': 'MACD Trading',
        'description': 'Uses MACD line crossovers and histogram for signals',
        'risk_level': 'Medium',
        'best_for': 'Trend following traders'
    },
    'ma_crossover': {
        'name': 'Moving Average Crossover',
        'description': 'Buys when fast MA crosses above slow MA',
        'risk_level': 'Medium',
        'best_for': 'Trend following traders'
    },
    'bollinger_bands': {
        'name': 'Bollinger Bands',
        'description': 'Trades based on price position relative to Bollinger Bands',
        'risk_level': 'Medium',
        'best_for': 'Mean reversion and breakout traders'
    },
    'range_trading': {
        'name': 'Range Trading',
        'description': 'Buys at support levels, sells at resistance levels',
        'risk_level': 'Medium',
        'best_for': 'Sideways market traders'
    },
    'grid_trading': {
        'name': 'Grid Trading',
        'description': 'Places buy/sell orders at regular price intervals',
        'risk_level': 'High',
        'best_for': 'High volatility markets'
    },
    'fear_greed': {
        'name': 'Fear & Greed Index',
        'description': 'Trades based on market sentiment indicators',
        'risk_level': 'High',
        'best_for': 'Contrarian traders'
    }
}

# Risk levels
RISK_LEVELS = {
    'Low': {
        'description': 'Conservative strategies with lower risk and returns',
        'max_drawdown': 0.1,
        'volatility': 0.15
    },
    'Medium': {
        'description': 'Balanced strategies with moderate risk and returns',
        'max_drawdown': 0.2,
        'volatility': 0.25
    },
    'High': {
        'description': 'Aggressive strategies with higher risk and potential returns',
        'max_drawdown': 0.4,
        'volatility': 0.4
    }
}
