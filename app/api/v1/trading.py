"""
Unified Trading API endpoints - Gestisce trading in base al trading_mode dell'utente.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.trading.unified_trading_service import unified_trading_service
from app.schemas.paper_trading import (
    PaperPortfolioCreate,
    PaperPortfolioResponse,
    PaperPositionResponse,
    TradeRequest,
    TradeResponse,
    TradeHistoryResponse,
    SetStopLossRequest,
    SetTakeProfitRequest,
    BalanceResponse,
    BalancesResponse,
    PortfolioSummaryResponse
)
from app.core.logging import get_logger
from decimal import Decimal

router = APIRouter()
logger = get_logger(__name__)


@router.post("/portfolios", response_model=PaperPortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PaperPortfolioCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Crea un nuovo portfolio.
    Il tipo (paper/live) è determinato dal trading_mode dell'utente impostato al login.
    """
    
    try:
        result = await unified_trading_service.create_portfolio(
            user=current_user,
            name=portfolio_data.name,
            initial_capital=portfolio_data.initial_capital,
            description=portfolio_data.description
        )
        
        logger.info(
            f"Portfolio created in {current_user.trading_mode.value} mode",
            portfolio_id=result['id'],
            user_id=current_user.id,
            mode=current_user.trading_mode.value
        )
        
        return PaperPortfolioResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to create portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portfolio: {str(e)}"
        )


@router.get("/portfolios", response_model=List[PaperPortfolioResponse])
async def get_all_portfolios(
    current_user: User = Depends(get_current_user)
):
    """Ottiene tutti i portfolio dell'utente corrente."""
    
    try:
        portfolios = await unified_trading_service.get_all_portfolios(user=current_user)
        
        return [PaperPortfolioResponse(**portfolio) for portfolio in portfolios]
        
    except Exception as e:
        logger.error(f"Failed to get portfolios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolios: {str(e)}"
        )


@router.get("/portfolios/{portfolio_id}", response_model=PaperPortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user)
):
    """Ottiene i dettagli di un portfolio."""
    
    try:
        result = await unified_trading_service.get_portfolio(
            user=current_user,
            portfolio_id=portfolio_id
        )
        
        return PaperPortfolioResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio: {str(e)}"
        )


@router.get("/portfolios/{portfolio_id}/positions", response_model=List[PaperPositionResponse])
async def get_portfolio_positions(
    portfolio_id: int,
    current_user: User = Depends(get_current_user)
):
    """Ottiene tutte le posizioni di un portfolio."""
    
    try:
        positions = await unified_trading_service.get_positions(
            user=current_user,
            portfolio_id=portfolio_id
        )
        
        return [PaperPositionResponse(**pos) for pos in positions]
        
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get positions: {str(e)}"
        )


@router.get("/portfolios/{portfolio_id}/balance")
async def get_portfolio_balance(
    portfolio_id: int,
    asset: str = None,
    current_user: User = Depends(get_current_user)
):
    """Ottiene il balance di un portfolio."""
    
    try:
        balance = await unified_trading_service.get_balance(
            user=current_user,
            portfolio_id=portfolio_id,
            asset=asset
        )
        
        if asset:
            return BalanceResponse(**balance)
        else:
            return BalancesResponse(**balance)
        
    except Exception as e:
        logger.error(f"Failed to get balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get balance: {str(e)}"
        )


@router.post("/portfolios/{portfolio_id}/buy", response_model=TradeResponse)
async def buy_asset(
    portfolio_id: int,
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Esegue un ordine di acquisto.
    Se l'utente è in paper mode, simula l'ordine.
    Se l'utente è in live mode, esegue l'ordine reale sull'exchange.
    """
    
    try:
        result = await unified_trading_service.buy(
            user=current_user,
            portfolio_id=portfolio_id,
            symbol=trade_data.symbol,
            quantity=trade_data.quantity,
            price=trade_data.price,
            order_type=trade_data.order_type
        )
        
        logger.info(
            f"Buy order executed in {current_user.trading_mode.value} mode",
            portfolio_id=portfolio_id,
            symbol=trade_data.symbol,
            quantity=float(trade_data.quantity),
            mode=current_user.trading_mode.value
        )
        
        return TradeResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to execute buy order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute buy order: {str(e)}"
        )


@router.post("/portfolios/{portfolio_id}/sell", response_model=TradeResponse)
async def sell_asset(
    portfolio_id: int,
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Esegue un ordine di vendita.
    Se l'utente è in paper mode, simula l'ordine.
    Se l'utente è in live mode, esegue l'ordine reale sull'exchange.
    """
    
    try:
        result = await unified_trading_service.sell(
            user=current_user,
            portfolio_id=portfolio_id,
            symbol=trade_data.symbol,
            quantity=trade_data.quantity,
            price=trade_data.price,
            order_type=trade_data.order_type
        )
        
        logger.info(
            f"Sell order executed in {current_user.trading_mode.value} mode",
            portfolio_id=portfolio_id,
            symbol=trade_data.symbol,
            quantity=float(trade_data.quantity),
            mode=current_user.trading_mode.value
        )
        
        return TradeResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to execute sell order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute sell order: {str(e)}"
        )


@router.get("/portfolios/{portfolio_id}/trades", response_model=List[TradeHistoryResponse])
async def get_trade_history(
    portfolio_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Ottiene lo storico dei trade."""
    
    try:
        trades = await unified_trading_service.get_trade_history(
            user=current_user,
            portfolio_id=portfolio_id,
            limit=limit
        )
        
        return [TradeHistoryResponse(**trade) for trade in trades]
        
    except Exception as e:
        logger.error(f"Failed to get trade history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trade history: {str(e)}"
        )


@router.post("/portfolios/{portfolio_id}/positions/{position_id}/close")
async def close_position(
    portfolio_id: int,
    position_id: int,
    current_user: User = Depends(get_current_user)
):
    """Chiude completamente una posizione."""
    
    try:
        result = await unified_trading_service.close_position(
            user=current_user,
            portfolio_id=portfolio_id,
            position_id=position_id
        )
        
        logger.info(
            f"Position closed in {current_user.trading_mode.value} mode",
            portfolio_id=portfolio_id,
            position_id=position_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to close position: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close position: {str(e)}"
        )


@router.put("/portfolios/{portfolio_id}/positions/{position_id}/stop-loss")
async def set_stop_loss(
    portfolio_id: int,
    position_id: int,
    request: SetStopLossRequest,
    current_user: User = Depends(get_current_user)
):
    """Imposta lo stop loss per una posizione."""
    
    try:
        result = await unified_trading_service.set_stop_loss(
            user=current_user,
            portfolio_id=portfolio_id,
            position_id=position_id,
            stop_loss_price=request.stop_loss_price
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to set stop loss: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set stop loss: {str(e)}"
        )


@router.put("/portfolios/{portfolio_id}/positions/{position_id}/take-profit")
async def set_take_profit(
    portfolio_id: int,
    position_id: int,
    request: SetTakeProfitRequest,
    current_user: User = Depends(get_current_user)
):
    """Imposta il take profit per una posizione."""
    
    try:
        result = await unified_trading_service.set_take_profit(
            user=current_user,
            portfolio_id=portfolio_id,
            position_id=position_id,
            take_profit_price=request.take_profit_price
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to set take profit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set take profit: {str(e)}"
        )


@router.post("/portfolios/{portfolio_id}/update-value", response_model=PortfolioSummaryResponse)
async def update_portfolio_value(
    portfolio_id: int,
    current_user: User = Depends(get_current_user)
):
    """Aggiorna il valore del portfolio in base ai prezzi di mercato correnti."""
    
    try:
        result = await unified_trading_service.update_portfolio_value(
            user=current_user,
            portfolio_id=portfolio_id
        )
        
        return PortfolioSummaryResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update portfolio value: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update portfolio value: {str(e)}"
        )

