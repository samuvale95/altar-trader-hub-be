"""
Exchange adapters package.
"""

from .base import BaseExchangeAdapter
from .binance import BinanceAdapter
from .kraken import KrakenAdapter
from .kucoin import KuCoinAdapter

__all__ = [
    "BaseExchangeAdapter",
    "BinanceAdapter", 
    "KrakenAdapter",
    "KuCoinAdapter",
    "get_exchange_adapter"
]


def get_exchange_adapter(exchange_name: str) -> BaseExchangeAdapter:
    """Get exchange adapter by name."""
    adapters = {
        "binance": BinanceAdapter,
        "kraken": KrakenAdapter,
        "kucoin": KuCoinAdapter,
    }
    
    if exchange_name.lower() not in adapters:
        raise ValueError(f"Unsupported exchange: {exchange_name}")
    
    return adapters[exchange_name.lower()]()
