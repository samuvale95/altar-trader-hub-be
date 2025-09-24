"""
Symbol Manager Service for dynamic symbol management from Binance.
"""

import requests
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.market_data import MarketData
import os

logger = get_logger(__name__)


class SymbolManager:
    """Service for managing trading symbols from Binance."""
    
    def __init__(self):
        self.binance_base_url = "https://api.binance.com/api/v3"
        self.symbols_cache_file = "data/binance_symbols_cache.json"
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
        
    def get_binance_symbols(self, quote_assets: List[str] = None) -> List[Dict[str, Any]]:
        """Get all trading symbols from Binance API."""
        
        try:
            logger.info("Fetching symbols from Binance API")
            response = requests.get(f"{self.binance_base_url}/exchangeInfo", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            symbols = data['symbols']
            
            # Filter active symbols only
            active_symbols = [
                symbol for symbol in symbols 
                if symbol['status'] == 'TRADING'
            ]
            
            # Filter by quote assets if specified
            if quote_assets:
                active_symbols = [
                    symbol for symbol in active_symbols
                    if symbol['quoteAsset'] in quote_assets
                ]
            
            logger.info(f"Retrieved {len(active_symbols)} active symbols")
            return active_symbols
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch symbols from Binance: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching symbols: {e}")
            return []
    
    def get_symbols_by_volume(self, limit: int = 100) -> List[str]:
        """Get top symbols by 24h volume."""
        
        try:
            logger.info(f"Fetching top {limit} symbols by volume")
            response = requests.get(f"{self.binance_base_url}/ticker/24hr", timeout=10)
            response.raise_for_status()
            
            ticker_data = response.json()
            
            # Sort by volume and get top symbols
            sorted_symbols = sorted(
                ticker_data, 
                key=lambda x: float(x['volume']), 
                reverse=True
            )
            
            top_symbols = [symbol['symbol'] for symbol in sorted_symbols[:limit]]
            logger.info(f"Retrieved top {len(top_symbols)} symbols by volume")
            
            return top_symbols
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch volume data: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching volume data: {e}")
            return []
    
    def get_popular_symbols(self, quote_asset: str = "USDT", limit: int = 50) -> List[str]:
        """Get popular symbols for a specific quote asset."""
        
        try:
            # Use cached symbols first
            symbols = self.get_cached_symbols([quote_asset])
            if not symbols:
                symbols = self.get_binance_symbols([quote_asset])
            
            if not symbols:
                return []
            
            # Get volume data
            volume_data = self.get_symbols_by_volume(1000)
            
            # Filter by quote asset and get top by volume
            quote_symbols = [s for s in volume_data if s.endswith(quote_asset)]
            
            return quote_symbols[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get popular symbols: {e}")
            return []
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists and is tradable on Binance."""
        
        try:
            # Check if symbol exists in our cache first
            cached_symbols = self._load_cached_symbols()
            if cached_symbols:
                symbol_exists = any(s['symbol'] == symbol for s in cached_symbols)
                if symbol_exists:
                    return True
            
            # If not in cache, check Binance API
            response = requests.get(
                f"{self.binance_base_url}/ticker/price",
                params={'symbol': symbol},
                timeout=5
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to validate symbol {symbol}: {e}")
            return False
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific symbol."""
        
        try:
            # Use cached symbols first
            symbols = self.get_cached_symbols()
            if not symbols:
                symbols = self.get_binance_symbols()
            
            symbol_info = next(
                (s for s in symbols if s['symbol'] == symbol), 
                None
            )
            
            if symbol_info:
                # Get current price
                price_response = requests.get(
                    f"{self.binance_base_url}/ticker/price",
                    params={'symbol': symbol},
                    timeout=5
                )
                
                if price_response.status_code == 200:
                    price_data = price_response.json()
                    symbol_info['current_price'] = float(price_data['price'])
                
                return symbol_info
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return None
    
    def refresh_symbols_cache(self) -> bool:
        """Refresh the symbols cache from Binance."""
        
        try:
            logger.info("Refreshing symbols cache")
            
            # Get all symbols
            symbols = self.get_binance_symbols()
            
            if not symbols:
                logger.warning("No symbols retrieved, keeping existing cache")
                return False
            
            # Create cache directory if it doesn't exist
            os.makedirs(os.path.dirname(self.symbols_cache_file), exist_ok=True)
            
            # Save to cache
            cache_data = {
                'symbols': symbols,
                'timestamp': datetime.utcnow().isoformat(),
                'count': len(symbols)
            }
            
            with open(self.symbols_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Symbols cache refreshed with {len(symbols)} symbols")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh symbols cache: {e}")
            return False
    
    def _load_cached_symbols(self) -> List[Dict[str, Any]]:
        """Load symbols from cache if available and not expired."""
        
        try:
            if not os.path.exists(self.symbols_cache_file):
                return []
            
            with open(self.symbols_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.utcnow() - cache_time > self.cache_duration:
                logger.info("Symbols cache expired")
                return []
            
            return cache_data['symbols']
            
        except Exception as e:
            logger.error(f"Failed to load cached symbols: {e}")
            return []
    
    def get_cached_symbols(self, quote_assets: List[str] = None) -> List[Dict[str, Any]]:
        """Get symbols from cache or refresh if needed."""
        
        # Try to load from cache first
        cached_symbols = self._load_cached_symbols()
        
        if cached_symbols:
            # Filter by quote assets if specified
            if quote_assets:
                cached_symbols = [
                    symbol for symbol in cached_symbols
                    if symbol['quoteAsset'] in quote_assets
                ]
            return cached_symbols
        
        # If no cache or expired, refresh
        logger.info("No valid cache found, refreshing symbols")
        if self.refresh_symbols_cache():
            return self._load_cached_symbols()
        
        return []
    
    def get_symbols_for_trading(self, strategy_type: str = "general") -> List[str]:
        """Get recommended symbols for trading based on strategy type."""
        
        # Strategy-specific symbol recommendations
        strategy_configs = {
            "general": {
                "quote_assets": ["USDT"],
                "limit": 50,
                "min_volume": 1000000  # 1M USDT
            },
            "scalping": {
                "quote_assets": ["USDT"],
                "limit": 20,
                "min_volume": 5000000  # 5M USDT
            },
            "swing": {
                "quote_assets": ["USDT", "BTC"],
                "limit": 30,
                "min_volume": 2000000  # 2M USDT
            },
            "long_term": {
                "quote_assets": ["USDT", "BTC", "ETH"],
                "limit": 15,
                "min_volume": 1000000  # 1M USDT
            }
        }
        
        config = strategy_configs.get(strategy_type, strategy_configs["general"])
        
        try:
            # Get popular symbols
            symbols = self.get_popular_symbols(
                quote_asset=config["quote_assets"][0],
                limit=config["limit"] * 2  # Get more to filter by volume
            )
            
            # Filter by minimum volume if specified
            if config.get("min_volume"):
                # This would require additional API calls to get volume data
                # For now, return the symbols as-is
                pass
            
            return symbols[:config["limit"]]
            
        except Exception as e:
            logger.error(f"Failed to get symbols for strategy {strategy_type}: {e}")
            return []
    
    def sync_with_database(self, db: Session) -> bool:
        """Sync available symbols with database."""
        
        try:
            logger.info("Syncing symbols with database")
            
            # Get current symbols from database
            db_symbols = db.query(MarketData.symbol).distinct().all()
            db_symbol_list = [row[0] for row in db_symbols]
            
            # Get Binance symbols
            binance_symbols = self.get_cached_symbols(["USDT"])
            binance_symbol_list = [s['symbol'] for s in binance_symbols]
            
            # Find new symbols
            new_symbols = set(binance_symbol_list) - set(db_symbol_list)
            
            if new_symbols:
                logger.info(f"Found {len(new_symbols)} new symbols: {list(new_symbols)[:10]}")
                # Here you could add logic to start collecting data for new symbols
            else:
                logger.info("No new symbols found")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync symbols with database: {e}")
            return False


# Global symbol manager instance
symbol_manager = SymbolManager()
