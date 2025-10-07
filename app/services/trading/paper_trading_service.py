"""
Paper Trading Service - Virtual portfolio management.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.paper_trading import PaperPortfolio, PaperPosition, PaperTrade, PaperBalance, TradingMode
from app.models.market_data import MarketData
from app.services.trading.base_trading_service import BaseTradingService

logger = get_logger(__name__)


class PaperTradingService(BaseTradingService):
    """Paper trading service for virtual portfolios."""
    
    def __init__(self):
        self.default_fee_percentage = Decimal("0.001")  # 0.1% trading fee
    
    async def create_portfolio(
        self,
        user_id: int,
        name: str,
        initial_capital: Decimal,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new paper trading portfolio."""
        
        db = SessionLocal()
        
        try:
            # Create portfolio
            portfolio = PaperPortfolio(
                user_id=user_id,
                name=name,
                description=description,
                mode=TradingMode.PAPER,
                initial_capital=initial_capital,
                cash_balance=initial_capital,
                total_value=initial_capital
            )
            
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)
            
            # Create initial USDT balance
            usdt_balance = PaperBalance(
                portfolio_id=portfolio.id,
                asset="USDT",
                free=initial_capital,
                total=initial_capital,
                usd_value=initial_capital
            )
            
            db.add(usdt_balance)
            db.commit()
            
            logger.info(f"Paper portfolio created", portfolio_id=portfolio.id, user_id=user_id, initial_capital=float(initial_capital))
            
            return {
                "id": portfolio.id,
                "name": portfolio.name,
                "mode": portfolio.mode.value,
                "initial_capital": float(portfolio.initial_capital),
                "cash_balance": float(portfolio.cash_balance),
                "total_value": float(portfolio.total_value),
                "created_at": portfolio.created_at.isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create paper portfolio: {e}")
            raise
        finally:
            db.close()
    
    async def get_portfolio(
        self,
        portfolio_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Get paper portfolio details."""
        
        db = SessionLocal()
        
        try:
            portfolio = db.query(PaperPortfolio).filter(
                PaperPortfolio.id == portfolio_id,
                PaperPortfolio.user_id == user_id
            ).first()
            
            if not portfolio:
                raise ValueError("Portfolio not found")
            
            # Update portfolio value before returning
            await self._update_portfolio_value_internal(portfolio, db)
            
            return {
                "id": portfolio.id,
                "name": portfolio.name,
                "description": portfolio.description,
                "mode": portfolio.mode.value,
                "initial_capital": float(portfolio.initial_capital),
                "cash_balance": float(portfolio.cash_balance),
                "invested_value": float(portfolio.invested_value),
                "total_value": float(portfolio.total_value),
                "total_pnl": float(portfolio.total_pnl),
                "total_pnl_percentage": float(portfolio.total_pnl_percentage),
                "realized_pnl": float(portfolio.realized_pnl),
                "unrealized_pnl": float(portfolio.unrealized_pnl),
                "total_trades": portfolio.total_trades,
                "winning_trades": portfolio.winning_trades,
                "losing_trades": portfolio.losing_trades,
                "win_rate": float(portfolio.win_rate),
                "max_drawdown": float(portfolio.max_drawdown) if portfolio.max_drawdown else 0,
                "created_at": portfolio.created_at.isoformat(),
                "updated_at": portfolio.updated_at.isoformat() if portfolio.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get paper portfolio: {e}")
            raise
        finally:
            db.close()
    
    async def get_balance(
        self,
        portfolio_id: int,
        asset: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get portfolio balance."""
        
        db = SessionLocal()
        
        try:
            if asset:
                balance = db.query(PaperBalance).filter(
                    PaperBalance.portfolio_id == portfolio_id,
                    PaperBalance.asset == asset.upper()
                ).first()
                
                if not balance:
                    return {
                        "asset": asset.upper(),
                        "free": 0,
                        "locked": 0,
                        "total": 0,
                        "usd_value": 0
                    }
                
                return {
                    "asset": balance.asset,
                    "free": float(balance.free),
                    "locked": float(balance.locked),
                    "total": float(balance.total),
                    "usd_value": float(balance.usd_value)
                }
            else:
                balances = db.query(PaperBalance).filter(
                    PaperBalance.portfolio_id == portfolio_id
                ).all()
                
                return {
                    "balances": [
                        {
                            "asset": b.asset,
                            "free": float(b.free),
                            "locked": float(b.locked),
                            "total": float(b.total),
                            "usd_value": float(b.usd_value)
                        }
                        for b in balances
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise
        finally:
            db.close()
    
    async def buy(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        order_type: str = "MARKET"
    ) -> Dict[str, Any]:
        """Execute buy order."""
        
        db = SessionLocal()
        
        try:
            # Get portfolio
            portfolio = db.query(PaperPortfolio).filter(
                PaperPortfolio.id == portfolio_id
            ).first()
            
            if not portfolio:
                raise ValueError("Portfolio not found")
            
            # Get current market price if not specified
            if price is None:
                price = await self._get_current_price(symbol, db)
            
            # Calculate costs
            total_value = quantity * price
            fee = total_value * self.default_fee_percentage
            total_cost = total_value + fee
            
            # Check if enough cash
            if portfolio.cash_balance < total_cost:
                raise ValueError(f"Insufficient funds. Need {total_cost}, have {portfolio.cash_balance}")
            
            # Update cash balance
            portfolio.cash_balance -= total_cost
            
            # Find or create position
            position = db.query(PaperPosition).filter(
                PaperPosition.portfolio_id == portfolio_id,
                PaperPosition.symbol == symbol,
                PaperPosition.is_active == True
            ).first()
            
            if position:
                # Update existing position (average down/up)
                total_quantity = position.quantity + quantity
                total_invested = (position.quantity * position.avg_entry_price) + total_value
                new_avg_price = total_invested / total_quantity
                
                position.quantity = total_quantity
                position.avg_entry_price = new_avg_price
                position.total_cost = position.total_cost + total_cost
            else:
                # Create new position
                position = PaperPosition(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    quantity=quantity,
                    avg_entry_price=price,
                    total_cost=total_cost,
                    current_price=price,
                    market_value=total_value
                )
                db.add(position)
            
            # Create trade record
            trade = PaperTrade(
                portfolio_id=portfolio_id,
                position_id=position.id if position.id else None,
                symbol=symbol,
                side="BUY",
                quantity=quantity,
                price=price,
                total_value=total_value,
                fee=fee,
                total_cost=total_cost,
                order_type=order_type,
                status="FILLED"
            )
            
            db.add(trade)
            
            # Update portfolio stats
            portfolio.total_trades += 1
            
            # Update balance
            await self._update_asset_balance(portfolio_id, symbol, quantity, "ADD", db)
            
            db.commit()
            db.refresh(trade)
            
            logger.info(f"Paper buy order executed", portfolio_id=portfolio_id, symbol=symbol, quantity=float(quantity), price=float(price))
            
            return {
                "trade_id": trade.id,
                "symbol": symbol,
                "side": "BUY",
                "quantity": float(quantity),
                "price": float(price),
                "total_cost": float(total_cost),
                "fee": float(fee),
                "status": "FILLED",
                "executed_at": trade.executed_at.isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to execute buy order: {e}")
            raise
        finally:
            db.close()
    
    async def sell(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        order_type: str = "MARKET"
    ) -> Dict[str, Any]:
        """Execute sell order."""
        
        db = SessionLocal()
        
        try:
            # Get position
            position = db.query(PaperPosition).filter(
                PaperPosition.portfolio_id == portfolio_id,
                PaperPosition.symbol == symbol,
                PaperPosition.is_active == True
            ).first()
            
            if not position:
                raise ValueError(f"No position found for {symbol}")
            
            if position.quantity < quantity:
                raise ValueError(f"Insufficient quantity. Have {position.quantity}, trying to sell {quantity}")
            
            # Get current market price if not specified
            if price is None:
                price = await self._get_current_price(symbol, db)
            
            # Calculate proceeds
            total_value = quantity * price
            fee = total_value * self.default_fee_percentage
            total_proceeds = total_value - fee
            
            # Calculate P&L
            cost_basis = quantity * position.avg_entry_price
            realized_pnl = total_value - cost_basis - fee
            realized_pnl_percentage = (realized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            # Get portfolio
            portfolio = db.query(PaperPortfolio).filter(
                PaperPortfolio.id == portfolio_id
            ).first()
            
            # Update cash balance
            portfolio.cash_balance += total_proceeds
            
            # Update position
            position.quantity -= quantity
            
            if position.quantity == 0:
                position.is_active = False
                position.closed_at = datetime.utcnow()
            
            # Create trade record
            trade = PaperTrade(
                portfolio_id=portfolio_id,
                position_id=position.id,
                symbol=symbol,
                side="SELL",
                quantity=quantity,
                price=price,
                total_value=total_value,
                fee=fee,
                total_cost=total_proceeds,
                realized_pnl=realized_pnl,
                realized_pnl_percentage=realized_pnl_percentage,
                order_type=order_type,
                status="FILLED"
            )
            
            db.add(trade)
            
            # Update portfolio stats
            portfolio.total_trades += 1
            portfolio.realized_pnl += realized_pnl
            
            if realized_pnl > 0:
                portfolio.winning_trades += 1
            else:
                portfolio.losing_trades += 1
            
            portfolio.win_rate = (portfolio.winning_trades / portfolio.total_trades * 100) if portfolio.total_trades > 0 else 0
            
            # Update balance
            await self._update_asset_balance(portfolio_id, symbol, quantity, "REMOVE", db)
            
            db.commit()
            db.refresh(trade)
            
            logger.info(f"Paper sell order executed", portfolio_id=portfolio_id, symbol=symbol, quantity=float(quantity), price=float(price), pnl=float(realized_pnl))
            
            return {
                "trade_id": trade.id,
                "symbol": symbol,
                "side": "SELL",
                "quantity": float(quantity),
                "price": float(price),
                "total_proceeds": float(total_proceeds),
                "fee": float(fee),
                "realized_pnl": float(realized_pnl),
                "realized_pnl_percentage": float(realized_pnl_percentage),
                "status": "FILLED",
                "executed_at": trade.executed_at.isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to execute sell order: {e}")
            raise
        finally:
            db.close()
    
    async def get_positions(
        self,
        portfolio_id: int
    ) -> List[Dict[str, Any]]:
        """Get all positions in portfolio."""
        
        db = SessionLocal()
        
        try:
            positions = db.query(PaperPosition).filter(
                PaperPosition.portfolio_id == portfolio_id,
                PaperPosition.is_active == True
            ).all()
            
            result = []
            for position in positions:
                # Update current price
                current_price = await self._get_current_price(position.symbol, db)
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                position.unrealized_pnl = position.market_value - position.total_cost
                position.unrealized_pnl_percentage = (
                    position.unrealized_pnl / position.total_cost * 100
                ) if position.total_cost > 0 else 0
                
                result.append({
                    "id": position.id,
                    "symbol": position.symbol,
                    "quantity": float(position.quantity),
                    "avg_entry_price": float(position.avg_entry_price),
                    "current_price": float(position.current_price),
                    "market_value": float(position.market_value),
                    "total_cost": float(position.total_cost),
                    "unrealized_pnl": float(position.unrealized_pnl),
                    "unrealized_pnl_percentage": float(position.unrealized_pnl_percentage),
                    "stop_loss_price": float(position.stop_loss_price) if position.stop_loss_price else None,
                    "take_profit_price": float(position.take_profit_price) if position.take_profit_price else None,
                    "opened_at": position.opened_at.isoformat()
                })
            
            db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
        finally:
            db.close()
    
    async def get_trade_history(
        self,
        portfolio_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trade history."""
        
        db = SessionLocal()
        
        try:
            trades = db.query(PaperTrade).filter(
                PaperTrade.portfolio_id == portfolio_id
            ).order_by(PaperTrade.executed_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": trade.id,
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "quantity": float(trade.quantity),
                    "price": float(trade.price),
                    "total_value": float(trade.total_value),
                    "fee": float(trade.fee),
                    "total_cost": float(trade.total_cost),
                    "realized_pnl": float(trade.realized_pnl) if trade.realized_pnl else 0,
                    "realized_pnl_percentage": float(trade.realized_pnl_percentage) if trade.realized_pnl_percentage else 0,
                    "order_type": trade.order_type,
                    "status": trade.status,
                    "executed_at": trade.executed_at.isoformat()
                }
                for trade in trades
            ]
            
        except Exception as e:
            logger.error(f"Failed to get trade history: {e}")
            raise
        finally:
            db.close()
    
    async def update_portfolio_value(
        self,
        portfolio_id: int
    ) -> Dict[str, Any]:
        """Update portfolio value based on current market prices."""
        
        db = SessionLocal()
        
        try:
            portfolio = db.query(PaperPortfolio).filter(
                PaperPortfolio.id == portfolio_id
            ).first()
            
            if not portfolio:
                raise ValueError("Portfolio not found")
            
            await self._update_portfolio_value_internal(portfolio, db)
            
            db.commit()
            db.refresh(portfolio)
            
            return {
                "portfolio_id": portfolio.id,
                "cash_balance": float(portfolio.cash_balance),
                "invested_value": float(portfolio.invested_value),
                "total_value": float(portfolio.total_value),
                "total_pnl": float(portfolio.total_pnl),
                "total_pnl_percentage": float(portfolio.total_pnl_percentage),
                "unrealized_pnl": float(portfolio.unrealized_pnl),
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update portfolio value: {e}")
            raise
        finally:
            db.close()
    
    async def close_position(
        self,
        portfolio_id: int,
        position_id: int
    ) -> Dict[str, Any]:
        """Close a position completely."""
        
        db = SessionLocal()
        
        try:
            position = db.query(PaperPosition).filter(
                PaperPosition.id == position_id,
                PaperPosition.portfolio_id == portfolio_id,
                PaperPosition.is_active == True
            ).first()
            
            if not position:
                raise ValueError("Position not found")
            
            # Sell entire position
            result = await self.sell(
                portfolio_id=portfolio_id,
                symbol=position.symbol,
                quantity=position.quantity,
                order_type="MARKET"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            raise
        finally:
            db.close()
    
    async def set_stop_loss(
        self,
        portfolio_id: int,
        position_id: int,
        stop_loss_price: Decimal
    ) -> Dict[str, Any]:
        """Set stop loss for a position."""
        
        db = SessionLocal()
        
        try:
            position = db.query(PaperPosition).filter(
                PaperPosition.id == position_id,
                PaperPosition.portfolio_id == portfolio_id
            ).first()
            
            if not position:
                raise ValueError("Position not found")
            
            position.stop_loss_price = stop_loss_price
            
            db.commit()
            
            logger.info(f"Stop loss set for position {position_id}: {float(stop_loss_price)}")
            
            return {
                "position_id": position_id,
                "symbol": position.symbol,
                "stop_loss_price": float(stop_loss_price),
                "message": "Stop loss set successfully"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to set stop loss: {e}")
            raise
        finally:
            db.close()
    
    async def set_take_profit(
        self,
        portfolio_id: int,
        position_id: int,
        take_profit_price: Decimal
    ) -> Dict[str, Any]:
        """Set take profit for a position."""
        
        db = SessionLocal()
        
        try:
            position = db.query(PaperPosition).filter(
                PaperPosition.id == position_id,
                PaperPosition.portfolio_id == portfolio_id
            ).first()
            
            if not position:
                raise ValueError("Position not found")
            
            position.take_profit_price = take_profit_price
            
            db.commit()
            
            logger.info(f"Take profit set for position {position_id}: {float(take_profit_price)}")
            
            return {
                "position_id": position_id,
                "symbol": position.symbol,
                "take_profit_price": float(take_profit_price),
                "message": "Take profit set successfully"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to set take profit: {e}")
            raise
        finally:
            db.close()
    
    # Private helper methods
    
    async def _get_current_price(self, symbol: str, db: Session) -> Decimal:
        """Get current market price for a symbol."""
        
        latest = db.query(MarketData).filter(
            MarketData.symbol == symbol
        ).order_by(MarketData.timestamp.desc()).first()
        
        if not latest:
            raise ValueError(f"No market data found for {symbol}")
        
        return latest.close_price
    
    async def _update_portfolio_value_internal(self, portfolio: PaperPortfolio, db: Session) -> None:
        """Update portfolio value (internal method with existing db session)."""
        
        # Get all active positions
        positions = db.query(PaperPosition).filter(
            PaperPosition.portfolio_id == portfolio.id,
            PaperPosition.is_active == True
        ).all()
        
        # Update each position's current value
        invested_value = Decimal(0)
        unrealized_pnl = Decimal(0)
        
        for position in positions:
            try:
                current_price = await self._get_current_price(position.symbol, db)
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                position.unrealized_pnl = position.market_value - position.total_cost
                position.unrealized_pnl_percentage = (
                    position.unrealized_pnl / position.total_cost * 100
                ) if position.total_cost > 0 else 0
                
                invested_value += position.market_value
                unrealized_pnl += position.unrealized_pnl
                
            except Exception as e:
                logger.warning(f"Failed to update price for {position.symbol}: {e}")
        
        # Update portfolio totals
        portfolio.invested_value = invested_value
        portfolio.total_value = portfolio.cash_balance + invested_value
        portfolio.unrealized_pnl = unrealized_pnl
        portfolio.total_pnl = portfolio.realized_pnl + unrealized_pnl
        portfolio.total_pnl_percentage = (
            portfolio.total_pnl / portfolio.initial_capital * 100
        ) if portfolio.initial_capital > 0 else 0
        
        # Calculate max drawdown
        if portfolio.total_value < portfolio.initial_capital:
            drawdown = (portfolio.initial_capital - portfolio.total_value) / portfolio.initial_capital * 100
            if drawdown > portfolio.max_drawdown:
                portfolio.max_drawdown = drawdown
    
    async def _update_asset_balance(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        action: str,  # ADD or REMOVE
        db: Session
    ) -> None:
        """Update asset balance in portfolio."""
        
        # Extract base asset from symbol (e.g., BTC from BTCUSDT)
        base_asset = symbol.replace("USDT", "").replace("BTC", "").replace("ETH", "")
        
        # Find or create balance
        balance = db.query(PaperBalance).filter(
            PaperBalance.portfolio_id == portfolio_id,
            PaperBalance.asset == base_asset
        ).first()
        
        if not balance:
            balance = PaperBalance(
                portfolio_id=portfolio_id,
                asset=base_asset,
                free=0,
                total=0
            )
            db.add(balance)
        
        if action == "ADD":
            balance.free += quantity
            balance.total += quantity
        elif action == "REMOVE":
            balance.free -= quantity
            balance.total -= quantity
        
        # Update USD value
        try:
            current_price = await self._get_current_price(f"{base_asset}USDT", db)
            balance.usd_value = balance.total * current_price
        except:
            # If can't get price, keep old value
            pass


# Global paper trading service instance
paper_trading_service = PaperTradingService()

