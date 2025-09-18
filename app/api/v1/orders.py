"""
Order management API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.order import Order, Trade
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    TradeResponse,
    OrderCancel,
    OrderStatusUpdate,
    OrderSummary,
    TradeSummary,
    OrderFilter,
    TradeFilter
)
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=List[OrderResponse])
def get_orders(
    filter_params: OrderFilter = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user orders with optional filtering."""
    
    # Base query
    query = db.query(Order).filter(Order.user_id == current_user.id)
    
    # Apply filters
    if filter_params.symbol:
        query = query.filter(Order.symbol == filter_params.symbol)
    
    if filter_params.side:
        query = query.filter(Order.side == filter_params.side)
    
    if filter_params.type:
        query = query.filter(Order.type == filter_params.type)
    
    if filter_params.status:
        query = query.filter(Order.status == filter_params.status)
    
    if filter_params.exchange:
        query = query.filter(Order.exchange == filter_params.exchange)
    
    if filter_params.strategy_id:
        query = query.filter(Order.strategy_id == filter_params.strategy_id)
    
    if filter_params.portfolio_id:
        query = query.filter(Order.portfolio_id == filter_params.portfolio_id)
    
    if filter_params.start_date:
        query = query.filter(Order.created_at >= filter_params.start_date)
    
    if filter_params.end_date:
        query = query.filter(Order.created_at <= filter_params.end_date)
    
    # Apply pagination
    orders = query.order_by(Order.created_at.desc()).offset(
        filter_params.offset
    ).limit(filter_params.limit).all()
    
    return orders


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new order."""
    
    # Generate client order ID
    import uuid
    client_order_id = f"order_{uuid.uuid4().hex[:16]}"
    
    # Create order
    order = Order(
        user_id=current_user.id,
        strategy_id=order_data.strategy_id,
        portfolio_id=order_data.portfolio_id,
        client_order_id=client_order_id,
        symbol=order_data.symbol,
        side=order_data.side,
        type=order_data.type,
        quantity=order_data.quantity,
        price=order_data.price,
        stop_price=order_data.stop_price,
        time_in_force=order_data.time_in_force,
        exchange=order_data.exchange,
        metadata=order_data.metadata
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    logger.info("Order created", order_id=order.id, user_id=current_user.id)
    
    # TODO: Send order to exchange
    # This would involve calling the appropriate exchange adapter
    
    return order


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific order."""
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_data: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an order."""
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if order can be updated
    if order.status not in ["pending", "partially_filled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be updated in current status"
        )
    
    # Update order fields
    for field, value in order_data.dict(exclude_unset=True).items():
        setattr(order, field, value)
    
    db.commit()
    db.refresh(order)
    
    logger.info("Order updated", order_id=order.id, user_id=current_user.id)
    
    return order


@router.delete("/{order_id}")
def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel an order."""
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if order can be cancelled
    if order.status not in ["pending", "partially_filled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be cancelled in current status"
        )
    
    # Cancel order
    order.status = "cancelled"
    order.cancelled_at = db.func.now()
    db.commit()
    
    logger.info("Order cancelled", order_id=order.id, user_id=current_user.id)
    
    # TODO: Send cancellation to exchange
    
    return {"message": "Order cancelled successfully"}


@router.get("/{order_id}/trades", response_model=List[TradeResponse])
def get_order_trades(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trades for a specific order."""
    
    # Verify order belongs to user
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Get trades
    trades = db.query(Trade).filter(
        Trade.order_id == order_id
    ).order_by(Trade.executed_at.desc()).all()
    
    return trades


@router.get("/trades/", response_model=List[TradeResponse])
def get_trades(
    filter_params: TradeFilter = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user trades with optional filtering."""
    
    # Base query with join to orders
    query = db.query(Trade).join(Order).filter(Order.user_id == current_user.id)
    
    # Apply filters
    if filter_params.symbol:
        query = query.filter(Trade.symbol == filter_params.symbol)
    
    if filter_params.side:
        query = query.filter(Trade.side == filter_params.side)
    
    if filter_params.exchange:
        query = query.filter(Trade.exchange == filter_params.exchange)
    
    if filter_params.order_id:
        query = query.filter(Trade.order_id == filter_params.order_id)
    
    if filter_params.start_date:
        query = query.filter(Trade.executed_at >= filter_params.start_date)
    
    if filter_params.end_date:
        query = query.filter(Trade.executed_at <= filter_params.end_date)
    
    # Apply pagination
    trades = query.order_by(Trade.executed_at.desc()).offset(
        filter_params.offset
    ).limit(filter_params.limit).all()
    
    return trades


@router.get("/summary/orders", response_model=OrderSummary)
def get_order_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get order summary statistics."""
    
    # Get all user orders
    orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    
    if not orders:
        return OrderSummary(
            total_orders=0,
            pending_orders=0,
            filled_orders=0,
            cancelled_orders=0,
            rejected_orders=0,
            total_volume=0,
            total_commission=0,
            total_pnl=0,
            win_rate=0
        )
    
    # Calculate statistics
    total_orders = len(orders)
    pending_orders = len([o for o in orders if o.status == "pending"])
    filled_orders = len([o for o in orders if o.status == "filled"])
    cancelled_orders = len([o for o in orders if o.status == "cancelled"])
    rejected_orders = len([o for o in orders if o.status == "rejected"])
    
    total_volume = sum(o.filled_quantity for o in orders if o.filled_quantity)
    total_commission = sum(o.commission for o in orders if o.commission)
    
    # Calculate P&L from trades
    trades = db.query(Trade).join(Order).filter(Order.user_id == current_user.id).all()
    total_pnl = sum(t.realized_pnl for t in trades if t.realized_pnl)
    
    # Calculate win rate
    winning_trades = len([t for t in trades if t.realized_pnl > 0])
    total_trades = len(trades)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    return OrderSummary(
        total_orders=total_orders,
        pending_orders=pending_orders,
        filled_orders=filled_orders,
        cancelled_orders=cancelled_orders,
        rejected_orders=rejected_orders,
        total_volume=total_volume,
        total_commission=total_commission,
        total_pnl=total_pnl,
        win_rate=win_rate
    )


@router.get("/summary/trades", response_model=TradeSummary)
def get_trade_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trade summary statistics."""
    
    # Get all user trades
    trades = db.query(Trade).join(Order).filter(Order.user_id == current_user.id).all()
    
    if not trades:
        return TradeSummary(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            total_volume=0,
            total_commission=0,
            total_pnl=0,
            avg_win=0,
            avg_loss=0,
            profit_factor=0,
            best_trade=0,
            worst_trade=0
        )
    
    # Calculate statistics
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.realized_pnl > 0])
    losing_trades = len([t for t in trades if t.realized_pnl < 0])
    
    total_volume = sum(t.quantity for t in trades)
    total_commission = sum(t.commission for t in trades)
    total_pnl = sum(t.realized_pnl for t in trades)
    
    # Calculate averages
    wins = [t.realized_pnl for t in trades if t.realized_pnl > 0]
    losses = [t.realized_pnl for t in trades if t.realized_pnl < 0]
    
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    # Calculate profit factor
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Best and worst trades
    pnls = [t.realized_pnl for t in trades if t.realized_pnl]
    best_trade = max(pnls) if pnls else 0
    worst_trade = min(pnls) if pnls else 0
    
    return TradeSummary(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        total_volume=total_volume,
        total_commission=total_commission,
        total_pnl=total_pnl,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        best_trade=best_trade,
        worst_trade=worst_trade
    )
