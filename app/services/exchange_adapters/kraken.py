"""
Kraken exchange adapter.
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


class KrakenAdapter(BaseExchangeAdapter):
    """Kraken exchange adapter."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.kraken.com"
        self.sandbox_url = "https://api-sandbox.kraken.com"
        self.ws_url = "wss://ws.kraken.com"
        self.sandbox_ws_url = "wss://ws-sandbox.kraken.com"
    
    def _get_base_url(self) -> str:
        """Get base URL based on sandbox mode."""
        return self.sandbox_url if self.sandbox else self.base_url
    
    def _get_ws_url(self) -> str:
        """Get WebSocket URL based on sandbox mode."""
        return self.sandbox_ws_url if self.sandbox else self.ws_url
    
    def _generate_signature(self, path: str, data: str) -> str:
        """Generate Kraken API signature."""
        message = path + hashlib.sha256(data.encode('utf-8')).digest()
        signature = hmac.new(
            base64.b64decode(self.secret_key),
            message,
            hashlib.sha512
        )
        return base64.b64encode(signature.digest()).decode('utf-8')
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Kraken API."""
        if data is None:
            data = {}
        
        url = f"{self._get_base_url()}{endpoint}"
        headers = self._get_headers()
        
        if signed:
            # Add nonce
            data['nonce'] = str(int(time.time() * 1000))
            
            # Generate signature
            postdata = urlencode(data)
            signature = self._generate_signature(endpoint, postdata)
            
            headers.update({
                'API-Key': self.api_key,
                'API-Sign': signature
            })
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=data, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, data=data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('error'):
                raise Exception(f"Kraken API error: {result['error']}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error("Kraken API request failed", error=str(e), endpoint=endpoint)
            raise
    
    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for Kraken (e.g., BTCUSDT -> XXBTZUSD)."""
        # Kraken uses different symbol format
        symbol_map = {
            'BTCUSDT': 'XXBTZUSD',
            'ETHUSDT': 'XETHZUSD',
            'ADAUSDT': 'ADAUSD',
            'DOTUSDT': 'DOTUSD',
            'LINKUSDT': 'LINKUSD'
        }
        return symbol_map.get(symbol.upper(), symbol.upper())
    
    def get_account_balances(self) -> List[Dict[str, Any]]:
        """Get account balances."""
        self._validate_credentials()
        
        response = self._make_request('POST', '/0/private/Balance', signed=True)
        
        balances = []
        for asset, balance in response['result'].items():
            if float(balance) > 0:
                balances.append({
                    'asset': asset,
                    'free': float(balance),
                    'locked': 0.0,  # Kraken doesn't separate free/locked
                    'total': float(balance)
                })
        
        return balances
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol."""
        symbol = self._format_symbol(symbol)
        
        response = self._make_request('GET', '/0/public/Ticker', {'pair': symbol})
        
        # Kraken returns data in a different format
        pair_data = list(response['result'].values())[0]
        
        return {
            'symbol': symbol,
            'price': float(pair_data['c'][0]),  # Last trade closed price
            'price_change': float(pair_data['c'][0]) - float(pair_data['o']),  # Last - Open
            'price_change_percent': 0,  # Calculate if needed
            'volume': float(pair_data['v'][1]),  # Volume today
            'quote_volume': 0,  # Not provided by Kraken
            'high': float(pair_data['h'][1]),  # High today
            'low': float(pair_data['l'][1]),  # Low today
            'open': float(pair_data['o']),  # Opening price today
            'close': float(pair_data['c'][0]),  # Last trade closed price
            'timestamp': self._format_timestamp(time.time())
        }
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get kline/candlestick data."""
        symbol = self._format_symbol(symbol)
        
        # Map interval to Kraken format
        interval_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080
        }
        
        kraken_interval = interval_map.get(interval, 60)
        
        params = {
            'pair': symbol,
            'interval': kraken_interval,
            'since': int(time.time() - (limit * kraken_interval * 60))
        }
        
        response = self._make_request('GET', '/0/public/OHLC', params)
        
        klines = []
        pair_data = list(response['result'].values())[0]
        
        for kline in pair_data:
            klines.append({
                'timestamp': self._format_timestamp(kline[0]),
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[6]),
                'quote_volume': 0,  # Not provided by Kraken
                'trades_count': 0,  # Not provided by Kraken
                'taker_buy_volume': 0,  # Not provided by Kraken
                'taker_buy_quote_volume': 0  # Not provided by Kraken
            })
        
        return klines
    
    def create_order(self, symbol: str, side: str, type: str, quantity: float, 
                   price: float = None, stop_price: float = None) -> Dict[str, Any]:
        """Create an order."""
        self._validate_credentials()
        
        symbol = self._format_symbol(symbol)
        
        data = {
            'pair': symbol,
            'type': side.lower(),
            'ordertype': type.lower(),
            'volume': str(quantity)
        }
        
        if price:
            data['price'] = str(price)
        
        if stop_price:
            data['stopprice'] = str(stop_price)
        
        response = self._make_request('POST', '/0/private/AddOrder', data, signed=True)
        
        result = response['result']
        
        return {
            'orderId': result['txid'][0] if result['txid'] else None,
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
        
        data = {
            'txid': order_id
        }
        
        response = self._make_request('POST', '/0/private/CancelOrder', data, signed=True)
        
        return {
            'orderId': order_id,
            'status': 'cancelled'
        }
    
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Get order details."""
        self._validate_credentials()
        
        data = {
            'txid': order_id
        }
        
        response = self._make_request('POST', '/0/private/QueryOrders', data, signed=True)
        
        result = response['result']
        order_data = result.get(order_id, {})
        
        return {
            'orderId': order_id,
            'symbol': order_data.get('descr', {}).get('pair', ''),
            'side': order_data.get('descr', {}).get('type', '').upper(),
            'type': order_data.get('descr', {}).get('ordertype', '').upper(),
            'quantity': float(order_data.get('vol', 0)),
            'price': float(order_data.get('descr', {}).get('price', 0)),
            'status': order_data.get('status', 'unknown'),
            'filled_quantity': float(order_data.get('vol_exec', 0)),
            'average_price': 0,  # Not provided by Kraken
            'timestamp': self._format_timestamp(order_data.get('opentm', time.time()))
        }
    
    def get_orders(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history."""
        self._validate_credentials()
        
        data = {}
        
        if symbol:
            data['trades'] = 'true'  # Include trades
        
        response = self._make_request('POST', '/0/private/OpenOrders', data, signed=True)
        
        orders = []
        result = response['result']
        
        for order_id, order_data in result.get('open', {}).items():
            orders.append({
                'orderId': order_id,
                'symbol': order_data.get('descr', {}).get('pair', ''),
                'side': order_data.get('descr', {}).get('type', '').upper(),
                'type': order_data.get('descr', {}).get('ordertype', '').upper(),
                'quantity': float(order_data.get('vol', 0)),
                'price': float(order_data.get('descr', {}).get('price', 0)),
                'status': order_data.get('status', 'unknown'),
                'filled_quantity': float(order_data.get('vol_exec', 0)),
                'average_price': 0,  # Not provided by Kraken
                'timestamp': self._format_timestamp(order_data.get('opentm', time.time()))
            })
        
        return orders
    
    def get_trades(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history."""
        self._validate_credentials()
        
        data = {}
        
        if symbol:
            data['pair'] = self._format_symbol(symbol)
        
        response = self._make_request('POST', '/0/private/TradesHistory', data, signed=True)
        
        trades = []
        result = response['result']
        
        for trade_id, trade_data in result.get('trades', {}).items():
            trades.append({
                'tradeId': trade_id,
                'orderId': trade_data.get('ordertxid', ''),
                'symbol': trade_data.get('pair', ''),
                'side': trade_data.get('type', '').upper(),
                'quantity': float(trade_data.get('vol', 0)),
                'price': float(trade_data.get('price', 0)),
                'commission': float(trade_data.get('fee', 0)),
                'commission_asset': trade_data.get('fee', ''),
                'timestamp': self._format_timestamp(trade_data.get('time', time.time()))
            })
        
        return trades
