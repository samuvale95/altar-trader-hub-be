"""
Unified Trading Service - Gestisce sia paper trading che live trading in base al trading_mode dell'utente.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.user import User, TradingMode
from app.services.trading.paper_trading_service import paper_trading_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class UnifiedTradingService:
    """
    Servizio unificato che gestisce trading paper e live.
    Controlla il trading_mode dell'utente per decidere quale servizio usare.
    """
    
    def __init__(self):
        self.paper_service = paper_trading_service
        # TODO: Aggiungere live_trading_service quando sarà implementato
        # self.live_service = live_trading_service
    
    def _get_service_for_user(self, user: User):
        """Restituisce il servizio corretto in base al trading_mode dell'utente."""
        if user.trading_mode == TradingMode.PAPER:
            logger.info("Using paper trading service", user_id=user.id)
            return self.paper_service
        else:
            # Per ora, anche live mode usa paper service
            # TODO: Implementare live trading service
            logger.warning("Live trading not yet implemented, using paper service", user_id=user.id)
            return self.paper_service
    
    async def create_portfolio(
        self,
        user: User,
        name: str,
        initial_capital: Decimal,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crea un nuovo portfolio."""
        service = self._get_service_for_user(user)
        return await service.create_portfolio(
            user_id=user.id,
            name=name,
            initial_capital=initial_capital,
            description=description
        )
    
    async def get_all_portfolios(
        self,
        user: User
    ) -> List[Dict[str, Any]]:
        """Ottiene tutti i portfolio dell'utente."""
        service = self._get_service_for_user(user)
        return await service.get_all_portfolios(user_id=user.id)
    
    async def get_portfolio(
        self,
        user: User,
        portfolio_id: int
    ) -> Dict[str, Any]:
        """Ottiene i dettagli di un portfolio."""
        service = self._get_service_for_user(user)
        return await service.get_portfolio(
            portfolio_id=portfolio_id,
            user_id=user.id
        )
    
    async def get_balance(
        self,
        user: User,
        portfolio_id: int,
        asset: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ottiene il balance del portfolio."""
        service = self._get_service_for_user(user)
        return await service.get_balance(
            portfolio_id=portfolio_id,
            asset=asset
        )
    
    async def buy(
        self,
        user: User,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        order_type: str = "MARKET"
    ) -> Dict[str, Any]:
        """Esegue un ordine di acquisto."""
        service = self._get_service_for_user(user)
        logger.info(
            f"Executing BUY order in {user.trading_mode.value} mode",
            user_id=user.id,
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=float(quantity)
        )
        return await service.buy(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_type=order_type
        )
    
    async def sell(
        self,
        user: User,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        order_type: str = "MARKET"
    ) -> Dict[str, Any]:
        """Esegue un ordine di vendita."""
        service = self._get_service_for_user(user)
        logger.info(
            f"Executing SELL order in {user.trading_mode.value} mode",
            user_id=user.id,
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=float(quantity)
        )
        return await service.sell(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_type=order_type
        )
    
    async def get_positions(
        self,
        user: User,
        portfolio_id: int
    ) -> List[Dict[str, Any]]:
        """Ottiene tutte le posizioni del portfolio."""
        service = self._get_service_for_user(user)
        return await service.get_positions(portfolio_id=portfolio_id)
    
    async def get_trade_history(
        self,
        user: User,
        portfolio_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Ottiene lo storico dei trade."""
        service = self._get_service_for_user(user)
        return await service.get_trade_history(
            portfolio_id=portfolio_id,
            limit=limit
        )
    
    async def update_portfolio_value(
        self,
        user: User,
        portfolio_id: int
    ) -> Dict[str, Any]:
        """Aggiorna il valore del portfolio."""
        service = self._get_service_for_user(user)
        return await service.update_portfolio_value(portfolio_id=portfolio_id)
    
    async def close_position(
        self,
        user: User,
        portfolio_id: int,
        position_id: int
    ) -> Dict[str, Any]:
        """Chiude una posizione."""
        service = self._get_service_for_user(user)
        return await service.close_position(
            portfolio_id=portfolio_id,
            position_id=position_id
        )
    
    async def set_stop_loss(
        self,
        user: User,
        portfolio_id: int,
        position_id: int,
        stop_loss_price: Decimal
    ) -> Dict[str, Any]:
        """Imposta lo stop loss per una posizione."""
        service = self._get_service_for_user(user)
        return await service.set_stop_loss(
            portfolio_id=portfolio_id,
            position_id=position_id,
            stop_loss_price=stop_loss_price
        )
    
    async def set_take_profit(
        self,
        user: User,
        portfolio_id: int,
        position_id: int,
        take_profit_price: Decimal
    ) -> Dict[str, Any]:
        """Imposta il take profit per una posizione."""
        service = self._get_service_for_user(user)
        return await service.set_take_profit(
            portfolio_id=portfolio_id,
            position_id=position_id,
            take_profit_price=take_profit_price
        )


# Global unified trading service instance
unified_trading_service = UnifiedTradingService()

