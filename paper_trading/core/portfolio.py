"""
Virtual Portfolio Simulator for Paper Trading
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


@dataclass
class Order:
    """Represents a trading order."""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: datetime = None
    status: OrderStatus = OrderStatus.PENDING
    strategy: str = ""
    reason: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Trade:
    """Represents an executed trade."""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    strategy: str
    reason: str
    commission: float = 0.0


class VirtualPortfolio:
    """Virtual portfolio for paper trading simulation."""
    
    def __init__(
        self, 
        initial_balance: float = 10000.0,
        base_currency: str = "USDT",
        commission_rate: float = 0.001  # 0.1% commission
    ):
        self.initial_balance = initial_balance
        self.base_currency = base_currency
        self.commission_rate = commission_rate
        
        # Portfolio state
        self.balance = initial_balance
        self.positions = {}  # {symbol: quantity}
        self.orders = []  # List of Order objects
        self.trades = []  # List of Trade objects
        
        # Performance tracking
        self.equity_history = []
        self.returns_history = []
        
        logger.info(f"Virtual portfolio initialized with {initial_balance} {base_currency}")
    
    def get_balance(self) -> float:
        """Get current balance."""
        return self.balance
    
    def get_position(self, symbol: str) -> float:
        """Get current position for a symbol."""
        return self.positions.get(symbol, 0.0)
    
    def get_total_equity(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio equity."""
        total_equity = self.balance
        
        for symbol, quantity in self.positions.items():
            if symbol in current_prices:
                total_equity += quantity * current_prices[symbol]
        
        return total_equity
    
    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET,
        strategy: str = "",
        reason: str = ""
    ) -> str:
        """Place a new order."""
        order_id = f"{symbol}_{side.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
            strategy=strategy,
            reason=reason
        )
        
        self.orders.append(order)
        logger.info(f"Order placed: {order_id} - {side.value} {quantity} {symbol} at {price or 'MARKET'}")
        
        return order_id
    
    def execute_order(self, order_id: str, current_price: float) -> bool:
        """Execute an order at current market price."""
        order = next((o for o in self.orders if o.id == order_id), None)
        if not order:
            logger.error(f"Order {order_id} not found")
            return False
        
        if order.status != OrderStatus.PENDING:
            logger.warning(f"Order {order_id} is not pending")
            return False
        
        # Calculate execution price
        if order.order_type == OrderType.MARKET:
            execution_price = current_price
        elif order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY and current_price <= order.price:
                execution_price = current_price
            elif order.side == OrderSide.SELL and current_price >= order.price:
                execution_price = current_price
            else:
                logger.info(f"Limit order {order_id} not executed - price not met")
                return False
        else:
            logger.error(f"Unsupported order type: {order.order_type}")
            return False
        
        # Calculate commission
        commission = order.quantity * execution_price * self.commission_rate
        
        # Check if we have enough balance for buy orders
        if order.side == OrderSide.BUY:
            total_cost = order.quantity * execution_price + commission
            if total_cost > self.balance:
                logger.warning(f"Insufficient balance for order {order_id}")
                order.status = OrderStatus.CANCELLED
                return False
        
        # Check if we have enough position for sell orders
        if order.side == OrderSide.SELL:
            if self.get_position(order.symbol) < order.quantity:
                logger.warning(f"Insufficient position for order {order_id}")
                order.status = OrderStatus.CANCELLED
                return False
        
        # Execute the trade
        trade = Trade(
            order_id=order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=execution_price,
            timestamp=datetime.now(),
            strategy=order.strategy,
            reason=order.reason,
            commission=commission
        )
        
        self.trades.append(trade)
        order.status = OrderStatus.FILLED
        
        # Update portfolio
        if order.side == OrderSide.BUY:
            self.balance -= (order.quantity * execution_price + commission)
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) + order.quantity
        else:  # SELL
            self.balance += (order.quantity * execution_price - commission)
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) - order.quantity
            
            # Remove position if quantity becomes zero
            if abs(self.positions[order.symbol]) < 1e-8:
                del self.positions[order.symbol]
        
        logger.info(f"Trade executed: {trade.side.value} {trade.quantity} {trade.symbol} at {trade.price}")
        return True
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict:
        """Get portfolio summary."""
        total_equity = self.get_total_equity(current_prices)
        total_return = (total_equity - self.initial_balance) / self.initial_balance
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_equity': total_equity,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'positions': self.positions.copy(),
            'total_trades': len(self.trades),
            'active_orders': len([o for o in self.orders if o.status == OrderStatus.PENDING])
        }
    
    def get_trades_dataframe(self) -> pd.DataFrame:
        """Get trades as DataFrame."""
        if not self.trades:
            return pd.DataFrame()
        
        data = []
        for trade in self.trades:
            data.append({
                'timestamp': trade.timestamp,
                'symbol': trade.symbol,
                'side': trade.side.value,
                'quantity': trade.quantity,
                'price': trade.price,
                'strategy': trade.strategy,
                'reason': trade.reason,
                'commission': trade.commission
            })
        
        return pd.DataFrame(data)
    
    def get_orders_dataframe(self) -> pd.DataFrame:
        """Get orders as DataFrame."""
        if not self.orders:
            return pd.DataFrame()
        
        data = []
        for order in self.orders:
            data.append({
                'id': order.id,
                'timestamp': order.timestamp,
                'symbol': order.symbol,
                'side': order.side.value,
                'order_type': order.order_type.value,
                'quantity': order.quantity,
                'price': order.price,
                'status': order.status.value,
                'strategy': order.strategy,
                'reason': order.reason
            })
        
        return pd.DataFrame(data)
    
    def update_equity_history(self, current_prices: Dict[str, float]):
        """Update equity history for performance tracking."""
        equity = self.get_total_equity(current_prices)
        self.equity_history.append({
            'timestamp': datetime.now(),
            'equity': equity
        })
        
        if len(self.equity_history) > 1:
            prev_equity = self.equity_history[-2]['equity']
            return_rate = (equity - prev_equity) / prev_equity
            self.returns_history.append(return_rate)
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics."""
        if not self.equity_history:
            return {}
        
        equity_df = pd.DataFrame(self.equity_history)
        equity_df.set_index('timestamp', inplace=True)
        
        # Calculate returns
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        # Basic metrics
        total_return = (equity_df['equity'].iloc[-1] - self.initial_balance) / self.initial_balance
        annualized_return = (1 + total_return) ** (252 / len(equity_df)) - 1
        
        # Volatility
        volatility = equity_df['returns'].std() * np.sqrt(252)
        
        # Sharpe ratio (assuming risk-free rate of 0)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        equity_df['cumulative'] = (1 + equity_df['returns']).cumprod()
        equity_df['running_max'] = equity_df['cumulative'].expanding().max()
        equity_df['drawdown'] = (equity_df['cumulative'] - equity_df['running_max']) / equity_df['running_max']
        max_drawdown = equity_df['drawdown'].min()
        
        # Win rate
        winning_trades = len([t for t in self.trades if t.side == OrderSide.BUY])
        total_trades = len(self.trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'annualized_return': annualized_return,
            'annualized_return_pct': annualized_return * 100,
            'volatility': volatility,
            'volatility_pct': volatility * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100
        }
