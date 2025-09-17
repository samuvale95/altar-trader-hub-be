"""
Binance exchange adapter.
"""

import hmac
import hashlib
import time
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from app.services.exchange_adapters.base import BaseExchangeAdapter
from app.core.logging import get_logger

logger = get_logger(__name__)


class BinanceAdapter(BaseExchangeAdapter):
    """Binance exchange adapter."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.binance.com"
        self.sandbox_url = "https://testnet.binance.vision"
        self.ws_url = "wss://stream.binance.com:9443/ws"
        self.sandbox_ws_url = "wss://testnet.binance.vision/ws"
    
    def _get_base_url(self) -> str:
        """Get base URL based on sandbox mode."""
        return self.sandbox_url if self.sandbox else self.base_url
    
    def _get_ws_url(self) -> str:
        """Get WebSocket URL based on sandbox mode."""
        return self.sandbox_ws_url if self.sandbox else self.ws_url
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature."""
        query_string = urlencode(params)
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Binance API."""
        if params is None:
            params = {}
        
        # Add timestamp for signed requests
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        url = f"{self._get_base_url()}{endpoint}"
        headers = self._get_headers()
        
        if signed:
            headers['X-MBX-APIKEY'] = self.api_key
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, params=params, headers=headers)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error("Binance API request failed", error=str(e), endpoint=endpoint)
            raise
    
    def get_account_balances(self) -> List[Dict[str, Any]]:
        """Get account balances."""
        self._validate_credentials()
        
        response = self._make_request('GET', '/api/v3/account', signed=True)
        
        balances = []
        for balance in response.get('balances', []):
            if float(balance['free']) > 0 or float(balance['locked']) > 0:
                balances.append({
                    'asset': balance['asset'],
                    'free': float(balance['free']),
                    'locked': float(balance['locked']),
                    'total': float(balance['free']) + float(balance['locked'])
                })
        
        return balances
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol."""
        symbol = self._format_symbol(symbol)
        
        response = self._make_request('GET', '/api/v3/ticker/24hr', {'symbol': symbol})
        
        return {
            'symbol': response['symbol'],
            'price': float(response['lastPrice']),
            'price_change': float(response['priceChange']),
            'price_change_percent': float(response['priceChangePercent']),
            'volume': float(response['volume']),
            'quote_volume': float(response['quoteVolume']),
            'high': float(response['highPrice']),
            'low': float(response['lowPrice']),
            'open': float(response['openPrice']),
            'close': float(response['lastPrice']),
            'timestamp': self._format_timestamp(response['closeTime'])
        }
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get kline/candlestick data."""
        symbol = self._format_symbol(symbol)
        
        # Map interval to Binance format
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1w'
        }
        
        binance_interval = interval_map.get(interval, interval)
        
        params = {
            'symbol': symbol,
            'interval': binance_interval,
            'limit': min(limit, 1000)
        }
        
        response = self._make_request('GET', '/api/v3/klines', params)
        
        klines = []
        for kline in response:
            klines.append({
                'timestamp': self._format_timestamp(kline[0]),
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5]),
                'quote_volume': float(kline[7]),
                'trades_count': int(kline[8]),
                'taker_buy_volume': float(kline[9]),
                'taker_buy_quote_volume': float(kline[10])
            })
        
        return klines
    
    def create_order(self, symbol: str, side: str, type: str, quantity: float, 
                   price: float = None, stop_price: float = None) -> Dict[str, Any]:
        """Create an order."""
        self._validate_credentials()
        
        symbol = self._format_symbol(symbol)
        
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': type.upper(),
            'quantity': quantity
        }
        
        if price:
            params['price'] = price
        
        if stop_price:
            params['stopPrice'] = stop_price
        
        # Set time in force
        if type.upper() == 'LIMIT':
            params['timeInForce'] = 'GTC'
        
        response = self._make_request('POST', '/api/v3/order', params, signed=True)
        
        return {
            'orderId': response['orderId'],
            'symbol': response['symbol'],
            'side': response['side'],
            'type': response['type'],
            'quantity': float(response['origQty']),
            'price': float(response.get('price', 0)),
            'status': response['status'],
            'timestamp': self._format_timestamp(response['transactTime'])
        }
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        self._validate_credentials()
        
        symbol = self._format_symbol(symbol)
        
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        response = self._make_request('DELETE', '/api/v3/order', params, signed=True)
        
        return {
            'orderId': response['orderId'],
            'symbol': response['symbol'],
            'status': response['status']
        }
    
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Get order details."""
        self._validate_credentials()
        
        symbol = self._format_symbol(symbol)
        
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        response = self._make_request('GET', '/api/v3/order', params, signed=True)
        
        return {
            'orderId': response['orderId'],
            'symbol': response['symbol'],
            'side': response['side'],
            'type': response['type'],
            'quantity': float(response['origQty']),
            'price': float(response.get('price', 0)),
            'status': response['status'],
            'filled_quantity': float(response['executedQty']),
            'average_price': float(response.get('avgPrice', 0)),
            'timestamp': self._format_timestamp(response['time'])
        }
    
    def get_orders(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history."""
        self._validate_credentials()
        
        params = {'limit': min(limit, 1000)}
        
        if symbol:
            params['symbol'] = self._format_symbol(symbol)
        
        response = self._make_request('GET', '/api/v3/allOrders', params, signed=True)
        
        orders = []
        for order in response:
            orders.append({
                'orderId': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'quantity': float(order['origQty']),
                'price': float(order.get('price', 0)),
                'status': order['status'],
                'filled_quantity': float(order['executedQty']),
                'average_price': float(order.get('avgPrice', 0)),
                'timestamp': self._format_timestamp(order['time'])
            })
        
        return orders
    
    def get_trades(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history."""
        self._validate_credentials()
        
        params = {'limit': min(limit, 1000)}
        
        if symbol:
            params['symbol'] = self._format_symbol(symbol)
        
        response = self._make_request('GET', '/api/v3/myTrades', params, signed=True)
        
        trades = []
        for trade in response:
            trades.append({
                'tradeId': trade['id'],
                'orderId': trade['orderId'],
                'symbol': trade['symbol'],
                'side': trade['isBuyer'] and 'BUY' or 'SELL',
                'quantity': float(trade['qty']),
                'price': float(trade['price']),
                'commission': float(trade['commission']),
                'commission_asset': trade['commissionAsset'],
                'timestamp': self._format_timestamp(trade['time'])
            })
        
        return trades
