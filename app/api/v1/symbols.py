"""
Symbols management API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.symbol_manager import symbol_manager
from app.services.data_feeder import data_feeder
from app.core.logging import get_logger
from pydantic import BaseModel

router = APIRouter()
logger = get_logger(__name__)


class SymbolInfo(BaseModel):
    """Symbol information response model."""
    symbol: str
    base_asset: str
    quote_asset: str
    status: str
    is_spot_trading_allowed: bool
    is_margin_trading_allowed: bool
    is_futures_trading_allowed: bool
    current_price: Optional[float] = None


class SymbolListResponse(BaseModel):
    """Symbol list response model."""
    symbols: List[str]
    total: int
    quote_asset: str
    last_updated: str


class SymbolValidationResponse(BaseModel):
    """Symbol validation response model."""
    symbol: str
    is_valid: bool
    is_tradable: bool
    message: str


@router.get("/available", response_model=SymbolListResponse)
def get_available_symbols(
    quote_asset: str = Query("USDT", description="Quote asset (USDT, BTC, ETH, BNB)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of symbols to return"),
    strategy_type: str = Query("general", description="Strategy type (general, scalping, swing, long_term)"),
    current_user: User = Depends(get_current_user)
):
    """Get available trading symbols from Binance."""
    
    try:
        logger.info(f"Getting available symbols for {quote_asset}, limit: {limit}")
        
        # Get symbols based on strategy type
        if strategy_type != "general":
            symbols = symbol_manager.get_symbols_for_trading(strategy_type)
        else:
            symbols = symbol_manager.get_popular_symbols(quote_asset, limit)
        
        if not symbols:
            # Fallback to data feeder
            symbols = data_feeder.get_available_symbols(quote_asset, limit)
        
        return SymbolListResponse(
            symbols=symbols,
            total=len(symbols),
            quote_asset=quote_asset,
            last_updated=symbol_manager._load_cached_symbols()[0].get('timestamp', 'Unknown') if symbol_manager._load_cached_symbols() else 'Unknown'
        )
        
    except Exception as e:
        logger.error(f"Failed to get available symbols: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve symbols: {str(e)}"
        )


@router.get("/info/{symbol}", response_model=SymbolInfo)
def get_symbol_info(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific symbol."""
    
    try:
        logger.info(f"Getting symbol info for {symbol}")
        
        symbol_info = symbol_manager.get_symbol_info(symbol)
        
        if not symbol_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Symbol {symbol} not found or not tradable"
            )
        
        return SymbolInfo(
            symbol=symbol_info['symbol'],
            base_asset=symbol_info['baseAsset'],
            quote_asset=symbol_info['quoteAsset'],
            status=symbol_info['status'],
            is_spot_trading_allowed=symbol_info['isSpotTradingAllowed'],
            is_margin_trading_allowed=symbol_info['isMarginTradingAllowed'],
            is_futures_trading_allowed=symbol_info.get('isFuturesTradingAllowed', False),
            current_price=symbol_info.get('current_price')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get symbol info for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve symbol info: {str(e)}"
        )


@router.get("/validate/{symbol}", response_model=SymbolValidationResponse)
def validate_symbol(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Validate if a symbol is available for trading."""
    
    try:
        logger.info(f"Validating symbol {symbol}")
        
        is_valid = symbol_manager.validate_symbol(symbol)
        is_tradable = symbol in data_feeder.symbols if hasattr(data_feeder, 'symbols') else False
        
        message = "Symbol is valid and tradable" if is_valid else "Symbol not found or not tradable"
        
        return SymbolValidationResponse(
            symbol=symbol,
            is_valid=is_valid,
            is_tradable=is_tradable,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Failed to validate symbol {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate symbol: {str(e)}"
        )


@router.post("/refresh")
def refresh_symbols(
    current_user: User = Depends(get_current_user)
):
    """Refresh the symbols list from Binance."""
    
    try:
        logger.info("Refreshing symbols from Binance")
        
        # Refresh symbols cache
        success = symbol_manager.refresh_symbols_cache()
        
        if success:
            # Update data feeder symbols
            data_feeder.symbols = data_feeder._load_dynamic_symbols()
            
            return {
                "message": "Symbols refreshed successfully",
                "success": True,
                "timestamp": symbol_manager._load_cached_symbols()[0].get('timestamp') if symbol_manager._load_cached_symbols() else None
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh symbols from Binance"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh symbols: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh symbols: {str(e)}"
        )


@router.get("/top-volume", response_model=List[str])
def get_top_volume_symbols(
    limit: int = Query(50, ge=1, le=200, description="Number of top symbols to return"),
    current_user: User = Depends(get_current_user)
):
    """Get top symbols by 24h volume."""
    
    try:
        logger.info(f"Getting top {limit} symbols by volume")
        
        symbols = symbol_manager.get_symbols_by_volume(limit)
        
        if not symbols:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to retrieve volume data from Binance"
            )
        
        return symbols
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get top volume symbols: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve top volume symbols: {str(e)}"
        )


@router.get("/by-strategy/{strategy_type}", response_model=List[str])
def get_symbols_by_strategy(
    strategy_type: str,
    current_user: User = Depends(get_current_user)
):
    """Get recommended symbols for a specific trading strategy."""
    
    try:
        logger.info(f"Getting symbols for strategy: {strategy_type}")
        
        symbols = symbol_manager.get_symbols_for_trading(strategy_type)
        
        if not symbols:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No symbols found for strategy type: {strategy_type}"
            )
        
        return symbols
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get symbols for strategy {strategy_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve symbols for strategy: {str(e)}"
        )


@router.get("/stats")
def get_symbols_stats(
    current_user: User = Depends(get_current_user)
):
    """Get symbols statistics."""
    
    try:
        logger.info("Getting symbols statistics")
        
        # Get cached symbols
        cached_symbols = symbol_manager.get_cached_symbols()
        
        if not cached_symbols:
            return {
                "total_symbols": 0,
                "usdt_pairs": 0,
                "btc_pairs": 0,
                "eth_pairs": 0,
                "bnb_pairs": 0,
                "last_updated": None,
                "cache_status": "No cache available"
            }
        
        # Count by quote asset
        usdt_count = len([s for s in cached_symbols if s['quoteAsset'] == 'USDT'])
        btc_count = len([s for s in cached_symbols if s['quoteAsset'] == 'BTC'])
        eth_count = len([s for s in cached_symbols if s['quoteAsset'] == 'ETH'])
        bnb_count = len([s for s in cached_symbols if s['quoteAsset'] == 'BNB'])
        
        return {
            "total_symbols": len(cached_symbols),
            "usdt_pairs": usdt_count,
            "btc_pairs": btc_count,
            "eth_pairs": eth_count,
            "bnb_pairs": bnb_count,
            "last_updated": cached_symbols[0].get('timestamp') if cached_symbols else None,
            "cache_status": "Available"
        }
        
    except Exception as e:
        logger.error(f"Failed to get symbols stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve symbols statistics: {str(e)}"
        )
