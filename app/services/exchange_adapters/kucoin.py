"""
KuCoin exchange adapter.
"""

import hmac
import hashlib
import base64
import time
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from app.services.exchange_adapters.base import BaseExchangeAdapter
from app.core.logging import get_logger

logger = get_logger(__name__)


class KuCoinAdapter(BaseExchangeAdapter):
    """KuCoin exchange adapter."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.kucoin.com"
        self.sandbox_url = "https://openapi-sandbox.kucoin.com"
        self.ws_url = "wss://ws-api.kucoin.com"
        self.sandbox_ws_url = "wss://ws-api-sandbox.kucoin.com"
    
    def _get_base_url(self) -> str:
        """Get base URL based on sandbox mode."""
        return self.sandbox_url if self.sandbox else self.base_url
    
    def _get_ws_url(self) -> str:
        """Get WebSocket URL based on sandbox mode."""
        return self.sandbox_ws_url if self.sandbox else self.ws_url
    
    def _generate_signature(self, timestamp: str, method: str, endpoint: str, body: str = "") -> str:
        """Generate KuCoin API signature."""
        message = timestamp + method + endpoint + body
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """Make HTTP request to KuCoin API."""
        if params is None:
            params = {}
        
        url = f"{self._get_base_url()}{endpoint}"
        headers = self._get_headers()
        
        if signed:
            timestamp = str(int(time.time() * 1000))
            body = urlencode(params) if method.upper() == 'POST' else ""
            signature = self._generate_signature(timestamp, method, endpoint, body)
            
            headers.update({
                'KC-API-KEY': self.api_key,
                'KC-API-SIGN': signature,
                'KC-API-TIMESTAMP': timestamp,
                'KC-API-PASSPHRASE': self.passphrase,
                'KC-API-KEY-VERSION': '2'
            })
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, data=params, headers=headers)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            if not result.get('code') == '200000':
                raise Exception(f"KuCoin API error: {result.get('msg', 'Unknown error')}")
            
            return result.get('data', {})
            
        except requests.exceptions.RequestException as e:
            logger.error("KuCoin API request failed", error=str(e), endpoint=endpoint)
            raise
    
    def get_account_balances(self) -> List[Dict[str, Any]]:
        """Get account balances."""
        self._validate_credentials()
        
        response = self._make_request('GET', '/api/v1/accounts', signed=True)
        
        balances = []
        for balance in response:
            if float(balance['balance']) > 0 or float(balance['available']) > 0:
                balances.append({
                    'asset': balance['currency'],
                    'free': float(balance['available']),
                    'locked': float(balance['balance']) - float(balance['available']),
                    'total': float(balance['balance'])
                })
        
        return balances
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol."""
        symbol = self._format_symbol(symbol)
        
        response = self._make_request('GET', '/api/v1/market/orderbook/level1', {'symbol': symbol})
        
        return {
            'symbol': response['symbol'],
            'price': float(response['price']),
            'price_change': 0,  # Not provided by KuCoin
            'price_change_percent': 0,  # Not provided by KuCoin
            'volume': float(response['size']),
            'quote_volume': 0,  # Not provided by KuCoin
            'high': 0,  # Not provided by KuCoin
            'low': 0,  # Not provided by KuCoin
            'open': 0,  # Not provided by KuCoin
            'close': float(response['price']),
            'timestamp': self._format_timestamp(response['time'])
        }
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get kline/candlestick data."""
        symbol = self._format_symbol(symbol)
        
        # Map interval to KuCoin format
        interval_map = {
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': '1hour',
            '4h': '4hour',
            '1d': '1day',
            '1w': '1week'
        }
        
        kucoin_interval = interval_map.get(interval, '1hour')
        
        params = {
            'symbol': symbol,
            'klineType': kucoin_interval
        }
        
        response = self._make_request('GET', '/api/v1/market/candles', params)
        
        klines = []
        for kline in response:
            klines.append({
                'timestamp': self._format_timestamp(kline[0]),
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5]),
                'quote_volume': 0,  # Not provided by KuCoin
                'trades_count': 0,  # Not provided by KuCoin
                'taker_buy_volume': 0,  # Not provided by KuCoin
                'taker_buy_quote_volume': 0  # Not provided by KuCoin
            })
        
        return klines
    
    def create_order(self, symbol: str, side: str, type: str, quantity: float, 
                   price: float = None, stop_price: float = None) -> Dict[str, Any]:
        """Create an order."""
        self._validate_credentials()
        
        symbol = self._format_symbol(symbol)
        
        params = {
            'clientOid': str(int(time.time() * 1000)),
            'side': side.lower(),
            'symbol': symbol,
            'type': type.lower(),
            'size': str(quantity)
        }
        
        if price:
            params['price'] = str(price)
        
        if stop_price:
            params['stopPrice'] = str(stop_price)
        
        response = self._make_request('POST', '/api/v1/orders', params, signed=True)
        
        return {
            'orderId': response['orderId'],
            'symbol': symbol,
            'side': side.upper(),
            'type': type.upper(),
            'quantity': quantity,
            'price': price,
            'status': 'pending',
            'timestamp': self._format_timestamp(time.time())
        }
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        self._validate_credentials()
        
        params = {
            'symbol': self._format_symbol(symbol),
            'orderId': order_id
        }
        
        response = self._make_request('DELETE', '/api/v1/orders', params, signed=True)
        
        return {
            'orderId': order_id,
            'status': 'cancelled'
        }
    
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Get order details."""
        self._validate_credentials()
        
        params = {
            'symbol': self._format_symbol(symbol),
            'orderId': order_id
        }
        
        response = self._make_request('GET', '/api/v1/orders', params, signed=True)
        
        return {
            'orderId': response['id'],
            'symbol': response['symbol'],
            'side': response['side'].upper(),
            'type': response['type'].upper(),
            'quantity': float(response['size']),
            'price': float(response.get('price', 0)),
            'status': response['status'],
            'filled_quantity': float(response.get('filledSize', 0)),
            'average_price': float(response.get('price', 0)),
            'timestamp': self._format_timestamp(response['createdAt'])
        }
    
    def get_orders(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history."""
        self._validate_credentials()
        
        params = {
            'pageSize': min(limit, 1000)
        }
        
        if symbol:
            params['symbol'] = self._format_symbol(symbol)
        
        response = self._make_request('GET', '/api/v1/orders', params, signed=True)
        
        orders = []
        for order in response.get('items', []):
            orders.append({
                'orderId': order['id'],
                'symbol': order['symbol'],
                'side': order['side'].upper(),
                'type': order['type'].upper(),
                'quantity': float(order['size']),
                'price': float(order.get('price', 0)),
                'status': order['status'],
                'filled_quantity': float(order.get('filledSize', 0)),
                'average_price': float(order.get('price', 0)),
                'timestamp': self._format_timestamp(order['createdAt'])
            })
        
        return orders
    
    def get_trades(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history."""
        self._validate_credentials()
        
        params = {
            'pageSize': min(limit, 1000)
        }
        
        if symbol:
            params['symbol'] = self._format_symbol(symbol)
        
        response = self._make_request('GET', '/api/v1/fills', params, signed=True)
        
        trades = []
        for trade in response.get('items', []):
            trades.append({
                'tradeId': trade['id'],
                'orderId': trade['orderId'],
                'symbol': trade['symbol'],
                'side': trade['side'].upper(),
                'quantity': float(trade['size']),
                'price': float(trade['price']),
                'commission': float(trade['fee']),
                'commission_asset': trade['feeCurrency'],
                'timestamp': self._format_timestamp(trade['createdAt'])
            })
        
        return trades
