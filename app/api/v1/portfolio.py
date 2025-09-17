"""
Portfolio API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.portfolio import Portfolio, Position, Balance
from app.schemas.portfolio import (
    PortfolioCreate, 
    PortfolioUpdate, 
    PortfolioResponse,
    PositionCreate,
    PositionUpdate,
    PositionResponse,
    BalanceResponse,
    PortfolioSummary,
    PositionSummary
)
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/overview", response_model=PortfolioSummary)
def get_portfolio_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio overview with summary statistics."""
    
    # Get user's portfolios
    portfolios = db.query(Portfolio).filter(
        Portfolio.user_id == current_user.id,
        Portfolio.is_active == True
    ).all()
    
    if not portfolios:
        return PortfolioSummary(
            total_value=0,
            total_pnl=0,
            total_pnl_percentage=0,
            active_positions=0,
            total_positions=0,
            winning_positions=0,
            losing_positions=0,
            win_rate=0
        )
    
    # Calculate summary statistics
    total_value = sum(p.total_value for p in portfolios)
    total_pnl = sum(p.total_pnl for p in portfolios)
    total_pnl_percentage = (total_pnl / total_value * 100) if total_value > 0 else 0
    
    # Get positions
    portfolio_ids = [p.id for p in portfolios]
    positions = db.query(Position).filter(
        Position.portfolio_id.in_(portfolio_ids),
        Position.is_active == True
    ).all()
    
    active_positions = len(positions)
    winning_positions = len([p for p in positions if p.unrealized_pnl > 0])
    losing_positions = len([p for p in positions if p.unrealized_pnl < 0])
    win_rate = (winning_positions / active_positions * 100) if active_positions > 0 else 0
    
    return PortfolioSummary(
        total_value=total_value,
        total_pnl=total_pnl,
        total_pnl_percentage=total_pnl_percentage,
        active_positions=active_positions,
        total_positions=len(positions),
        winning_positions=winning_positions,
        losing_positions=losing_positions,
        win_rate=win_rate
    )


@router.get("/portfolios", response_model=List[PortfolioResponse])
def get_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user portfolios."""
    
    portfolios = db.query(Portfolio).filter(
        Portfolio.user_id == current_user.id
    ).all()
    
    return portfolios


@router.post("/portfolios", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new portfolio."""
    
    # Check if portfolio name already exists for user
    existing_portfolio = db.query(Portfolio).filter(
        Portfolio.user_id == current_user.id,
        Portfolio.name == portfolio_data.name
    ).first()
    
    if existing_portfolio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio name already exists"
        )
    
    # Create portfolio
    portfolio = Portfolio(
        user_id=current_user.id,
        name=portfolio_data.name,
        description=portfolio_data.description
    )
    
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    logger.info("Portfolio created", portfolio_id=portfolio.id, user_id=current_user.id)
    
    return portfolio


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific portfolio."""
    
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return portfolio


@router.put("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: int,
    portfolio_data: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a portfolio."""
    
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Update portfolio fields
    for field, value in portfolio_data.dict(exclude_unset=True).items():
        setattr(portfolio, field, value)
    
    db.commit()
    db.refresh(portfolio)
    
    logger.info("Portfolio updated", portfolio_id=portfolio.id, user_id=current_user.id)
    
    return portfolio


@router.delete("/portfolios/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a portfolio."""
    
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Deactivate portfolio instead of deleting
    portfolio.is_active = False
    db.commit()
    
    logger.info("Portfolio deleted", portfolio_id=portfolio.id, user_id=current_user.id)
    
    return {"message": "Portfolio deleted successfully"}


@router.get("/positions", response_model=List[PositionResponse])
def get_positions(
    portfolio_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all positions for user's portfolios."""
    
    # Get user's portfolio IDs
    portfolio_ids = db.query(Portfolio.id).filter(
        Portfolio.user_id == current_user.id
    ).all()
    portfolio_ids = [p[0] for p in portfolio_ids]
    
    if not portfolio_ids:
        return []
    
    # Filter by portfolio if specified
    query = db.query(Position).filter(Position.portfolio_id.in_(portfolio_ids))
    
    if portfolio_id:
        if portfolio_id not in portfolio_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        query = query.filter(Position.portfolio_id == portfolio_id)
    
    positions = query.all()
    
    return positions


@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(
    position_data: PositionCreate,
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new position."""
    
    # Verify portfolio belongs to user
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Create position
    position = Position(
        portfolio_id=portfolio_id,
        symbol=position_data.symbol,
        base_asset=position_data.symbol.split('USDT')[0],  # Extract base asset
        quote_asset='USDT',  # Default quote asset
        quantity=position_data.quantity,
        avg_price=position_data.avg_price,
        stop_loss_price=position_data.stop_loss_price,
        take_profit_price=position_data.take_profit_price,
        max_loss=position_data.max_loss
    )
    
    db.add(position)
    db.commit()
    db.refresh(position)
    
    logger.info("Position created", position_id=position.id, portfolio_id=portfolio_id)
    
    return position


@router.get("/balances", response_model=List[BalanceResponse])
def get_balances(
    portfolio_id: Optional[int] = None,
    exchange: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all balances for user's portfolios."""
    
    # Get user's portfolio IDs
    portfolio_ids = db.query(Portfolio.id).filter(
        Portfolio.user_id == current_user.id
    ).all()
    portfolio_ids = [p[0] for p in portfolio_ids]
    
    if not portfolio_ids:
        return []
    
    # Filter by portfolio if specified
    query = db.query(Balance).filter(Balance.portfolio_id.in_(portfolio_ids))
    
    if portfolio_id:
        if portfolio_id not in portfolio_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        query = query.filter(Balance.portfolio_id == portfolio_id)
    
    if exchange:
        query = query.filter(Balance.exchange == exchange)
    
    balances = query.all()
    
    return balances
