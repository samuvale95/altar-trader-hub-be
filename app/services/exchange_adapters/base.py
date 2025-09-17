"""
Base exchange adapter class.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class BaseExchangeAdapter(ABC):
    """Base class for exchange adapters."""
    
    def __init__(self):
        self.api_key = None
        self.secret_key = None
        self.passphrase = None
        self.sandbox = True
        self.base_url = None
        self.ws_url = None
    
    def set_credentials(self, api_key: str, secret_key: str, passphrase: str = None):
        """Set API credentials."""
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
    
    def set_sandbox(self, sandbox: bool):
        """Set sandbox mode."""
        self.sandbox = sandbox
    
    @abstractmethod
    def get_account_balances(self) -> List[Dict[str, Any]]:
        """Get account balances."""
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol."""
        pass
    
    @abstractmethod
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get kline/candlestick data."""
        pass
    
    @abstractmethod
    def create_order(self, symbol: str, side: str, type: str, quantity: float, 
                   price: float = None, stop_price: float = None) -> Dict[str, Any]:
        """Create an order."""
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        pass
    
    @abstractmethod
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Get order details."""
        pass
    
    @abstractmethod
    def get_orders(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history."""
        pass
    
    @abstractmethod
    def get_trades(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history."""
        pass
    
    def _format_timestamp(self, timestamp: Any) -> datetime:
        """Format timestamp to datetime object."""
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        elif isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return timestamp
    
    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for exchange."""
        return symbol.upper()
    
    def _validate_credentials(self):
        """Validate API credentials."""
        if not self.api_key or not self.secret_key:
            raise ValueError("API credentials not set")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Content-Type": "application/json",
            "User-Agent": "AltarTraderHub/1.0"
        }
