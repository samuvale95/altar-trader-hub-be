"""
Paper Trading API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.trading.paper_trading_service import paper_trading_service
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


@router.post("/portfolio", response_model=PaperPortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_paper_portfolio(
    portfolio_data: PaperPortfolioCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new paper trading portfolio."""
    
    try:
        result = await paper_trading_service.create_portfolio(
            user_id=current_user.id,
            name=portfolio_data.name,
            initial_capital=portfolio_data.initial_capital,
            description=portfolio_data.description
        )
        
        logger.info(f"Paper portfolio created", portfolio_id=result['id'], user_id=current_user.id)
        
        return PaperPortfolioResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to create paper portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create paper portfolio: {str(e)}"
        )


@router.get("/portfolios", response_model=List[PaperPortfolioResponse])
async def get_all_portfolios(
    current_user: User = Depends(get_current_user)
):
    """Get all paper portfolios for the current user."""
    
    try:
        portfolios = await paper_trading_service.get_all_portfolios(user_id=current_user.id)
        
        return [PaperPortfolioResponse(**portfolio) for portfolio in portfolios]
        
    except Exception as e:
        logger.error(f"Failed to get portfolios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolios: {str(e)}"
        )


@router.get("/portfolio/{portfolio_id}", response_model=PaperPortfolioResponse)
async def get_paper_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get paper portfolio details."""
    
    try:
        result = await paper_trading_service.get_portfolio(
            portfolio_id=portfolio_id,
            user_id=current_user.id
        )
        
        return PaperPortfolioResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get paper portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get paper portfolio: {str(e)}"
        )


@router.get("/portfolio/{portfolio_id}/positions", response_model=List[PaperPositionResponse])
async def get_portfolio_positions(
    portfolio_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get all positions in portfolio."""
    
    try:
        positions = await paper_trading_service.get_positions(portfolio_id=portfolio_id)
        
        return [PaperPositionResponse(**pos) for pos in positions]
        
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get positions: {str(e)}"
        )


@router.get("/portfolio/{portfolio_id}/balance")
async def get_portfolio_balance(
    portfolio_id: int,
    asset: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get portfolio balance."""
    
    try:
        balance = await paper_trading_service.get_balance(
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


@router.post("/portfolio/{portfolio_id}/buy", response_model=TradeResponse)
async def buy_asset(
    portfolio_id: int,
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute a buy order."""
    
    try:
        result = await paper_trading_service.buy(
            portfolio_id=portfolio_id,
            symbol=trade_data.symbol,
            quantity=trade_data.quantity,
            price=trade_data.price,
            order_type=trade_data.order_type
        )
        
        logger.info(f"Paper buy order executed", portfolio_id=portfolio_id, symbol=trade_data.symbol, quantity=float(trade_data.quantity))
        
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


@router.post("/portfolio/{portfolio_id}/sell", response_model=TradeResponse)
async def sell_asset(
    portfolio_id: int,
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute a sell order."""
    
    try:
        result = await paper_trading_service.sell(
            portfolio_id=portfolio_id,
            symbol=trade_data.symbol,
            quantity=trade_data.quantity,
            price=trade_data.price,
            order_type=trade_data.order_type
        )
        
        logger.info(f"Paper sell order executed", portfolio_id=portfolio_id, symbol=trade_data.symbol, quantity=float(trade_data.quantity))
        
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


@router.get("/portfolio/{portfolio_id}/trades", response_model=List[TradeHistoryResponse])
async def get_trade_history(
    portfolio_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get trade history for portfolio."""
    
    try:
        trades = await paper_trading_service.get_trade_history(
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


@router.post("/portfolio/{portfolio_id}/position/{position_id}/close")
async def close_position(
    portfolio_id: int,
    position_id: int,
    current_user: User = Depends(get_current_user)
):
    """Close a position completely."""
    
    try:
        result = await paper_trading_service.close_position(
            portfolio_id=portfolio_id,
            position_id=position_id
        )
        
        logger.info(f"Position closed", portfolio_id=portfolio_id, position_id=position_id)
        
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


@router.put("/portfolio/{portfolio_id}/position/{position_id}/stop-loss")
async def set_stop_loss(
    portfolio_id: int,
    position_id: int,
    request: SetStopLossRequest,
    current_user: User = Depends(get_current_user)
):
    """Set stop loss for a position."""
    
    try:
        result = await paper_trading_service.set_stop_loss(
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


@router.put("/portfolio/{portfolio_id}/position/{position_id}/take-profit")
async def set_take_profit(
    portfolio_id: int,
    position_id: int,
    request: SetTakeProfitRequest,
    current_user: User = Depends(get_current_user)
):
    """Set take profit for a position."""
    
    try:
        result = await paper_trading_service.set_take_profit(
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


@router.post("/portfolio/{portfolio_id}/update-value", response_model=PortfolioSummaryResponse)
async def update_portfolio_value(
    portfolio_id: int,
    current_user: User = Depends(get_current_user)
):
    """Update portfolio value based on current market prices."""
    
    try:
        result = await paper_trading_service.update_portfolio_value(portfolio_id=portfolio_id)
        
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

