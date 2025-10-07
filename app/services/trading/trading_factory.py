"""
Trading Factory - Switch between paper and live trading.
"""

from typing import Optional
from app.core.logging import get_logger
from app.services.trading.base_trading_service import BaseTradingService
from app.services.trading.paper_trading_service import PaperTradingService
from app.services.trading.live_trading_service import LiveTradingService
from app.models.paper_trading import TradingMode

logger = get_logger(__name__)


class TradingFactory:
    """Factory for creating trading service instances."""
    
    @staticmethod
    def get_trading_service(
        mode: TradingMode = TradingMode.PAPER,
        exchange: str = "binance",
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        passphrase: Optional[str] = None
    ) -> BaseTradingService:
        """
        Get trading service based on mode.
        
        Args:
            mode: Trading mode (PAPER or LIVE)
            exchange: Exchange name (for live trading)
            api_key: API key (for live trading)
            secret_key: Secret key (for live trading)
            passphrase: Passphrase (for live trading, some exchanges)
        
        Returns:
            Trading service instance (Paper or Live)
        """
        
        if mode == TradingMode.PAPER:
            logger.info("Creating paper trading service")
            return PaperTradingService()
        
        elif mode == TradingMode.LIVE:
            logger.info(f"Creating live trading service for {exchange}")
            
            if not api_key or not secret_key:
                raise ValueError("API credentials required for live trading")
            
            service = LiveTradingService(exchange=exchange)
            service.set_credentials(api_key, secret_key, passphrase)
            
            return service
        
        else:
            raise ValueError(f"Invalid trading mode: {mode}")
    
    @staticmethod
    def get_default_service() -> BaseTradingService:
        """Get default trading service (paper trading)."""
        return PaperTradingService()


# Convenience function
def get_trading_service(mode: str = "paper", **kwargs) -> BaseTradingService:
    """
    Convenience function to get trading service.
    
    Usage:
        # Paper trading (default)
        service = get_trading_service()
        
        # Live trading
        service = get_trading_service(
            mode="live",
            exchange="binance",
            api_key="your_key",
            secret_key="your_secret"
        )
    """
    
    mode_enum = TradingMode.PAPER if mode.lower() == "paper" else TradingMode.LIVE
    
    return TradingFactory.get_trading_service(mode=mode_enum, **kwargs)

