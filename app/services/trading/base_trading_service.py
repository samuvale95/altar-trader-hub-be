"""
Base trading service interface for paper and live trading.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime


class BaseTradingService(ABC):
    """Abstract base class for trading services."""
    
    @abstractmethod
    async def create_portfolio(
        self,
        user_id: int,
        name: str,
        initial_capital: Decimal,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new portfolio."""
        pass
    
    @abstractmethod
    async def get_portfolio(
        self,
        portfolio_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Get portfolio details."""
        pass
    
    @abstractmethod
    async def get_balance(
        self,
        portfolio_id: int,
        asset: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get portfolio balance."""
        pass
    
    @abstractmethod
    async def buy(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        order_type: str = "MARKET"
    ) -> Dict[str, Any]:
        """Execute buy order."""
        pass
    
    @abstractmethod
    async def sell(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        order_type: str = "MARKET"
    ) -> Dict[str, Any]:
        """Execute sell order."""
        pass
    
    @abstractmethod
    async def get_positions(
        self,
        portfolio_id: int
    ) -> List[Dict[str, Any]]:
        """Get all positions in portfolio."""
        pass
    
    @abstractmethod
    async def get_trade_history(
        self,
        portfolio_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trade history."""
        pass
    
    @abstractmethod
    async def update_portfolio_value(
        self,
        portfolio_id: int
    ) -> Dict[str, Any]:
        """Update portfolio value based on current market prices."""
        pass
    
    @abstractmethod
    async def close_position(
        self,
        portfolio_id: int,
        position_id: int
    ) -> Dict[str, Any]:
        """Close a position."""
        pass
    
    @abstractmethod
    async def set_stop_loss(
        self,
        portfolio_id: int,
        position_id: int,
        stop_loss_price: Decimal
    ) -> Dict[str, Any]:
        """Set stop loss for a position."""
        pass
    
    @abstractmethod
    async def set_take_profit(
        self,
        portfolio_id: int,
        position_id: int,
        take_profit_price: Decimal
    ) -> Dict[str, Any]:
        """Set take profit for a position."""
        pass

