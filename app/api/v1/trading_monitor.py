"""
Trading Monitor API endpoints for real-time monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import asyncio
import logging
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.trading_strategy import TradingStrategy, StrategyStatus
from app.schemas.trading_strategy import StrategyPerformanceMetrics
from app.services.trading_strategy_service import TradingStrategyService
from app.services.paper_trading_integration import PaperTradingIntegrationService

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove broken connections
                    self.active_connections[user_id].remove(connection)
    
    async def broadcast_to_user(self, data: Dict[str, Any], user_id: int):
        message = json.dumps(data, default=str)
        await self.send_personal_message(message, user_id)

manager = ConnectionManager()


@router.get("/strategies/active", response_model=List[Dict[str, Any]])
async def get_active_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active strategies for the user."""
    service = TradingStrategyService(db)
    strategies = service.get_strategies(
        current_user.id, 
        status=StrategyStatus.ACTIVE
    )
    
    return [
        {
            "id": strategy.id,
            "name": strategy.name,
            "strategy_type": strategy.strategy_type.value,
            "symbol": strategy.symbol,
            "timeframe": strategy.timeframe,
            "status": strategy.status.value,
            "is_active": strategy.is_active,
            "current_balance": float(strategy.current_balance),
            "total_equity": float(strategy.total_equity),
            "total_return": float(strategy.total_return),
            "total_trades": strategy.total_trades,
            "win_rate": float(strategy.win_rate),
            "last_run_at": strategy.last_run_at.isoformat() if strategy.last_run_at else None,
            "started_at": strategy.started_at.isoformat() if strategy.started_at else None
        }
        for strategy in strategies
    ]


@router.get("/strategies/{strategy_id}/performance", response_model=Dict[str, Any])
async def get_strategy_performance_realtime(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time performance data for a strategy."""
    integration_service = PaperTradingIntegrationService(db)
    performance_data = integration_service.get_strategy_performance_data(
        strategy_id, 
        current_user.id, 
        days=30
    )
    
    if not performance_data:
        raise HTTPException(status_code=404, detail="Strategy not found or no data available")
    
    return performance_data


@router.get("/strategies/{strategy_id}/trades/recent", response_model=List[Dict[str, Any]])
async def get_recent_trades(
    strategy_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent trades for a strategy."""
    service = TradingStrategyService(db)
    trades = service.get_strategy_trades(strategy_id, current_user.id, limit=limit)
    
    return [
        {
            "id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": float(trade.quantity),
            "price": float(trade.price),
            "commission": float(trade.commission),
            "signal_strength": float(trade.signal_strength),
            "reason": trade.reason,
            "executed_at": trade.executed_at.isoformat()
        }
        for trade in trades
    ]


@router.get("/dashboard/overview", response_model=Dict[str, Any])
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard overview data."""
    service = TradingStrategyService(db)
    integration_service = PaperTradingIntegrationService(db)
    
    # Get statistics
    stats = service.get_strategy_statistics(current_user.id)
    
    # Get active strategies
    active_strategies = service.get_strategies(
        current_user.id, 
        status=StrategyStatus.ACTIVE,
        limit=5
    )
    
    # Get recent backtests
    recent_backtests = service.get_backtest_results(
        current_user.id, 
        limit=5
    )
    
    return {
        "statistics": {
            "total_strategies": stats.total_strategies,
            "active_strategies": stats.active_strategies,
            "total_backtests": stats.total_backtests,
            "running_backtests": stats.running_backtests,
            "total_trades": stats.total_trades,
            "total_profit": float(stats.total_profit),
            "best_strategy": stats.best_strategy,
            "worst_strategy": stats.worst_strategy
        },
        "active_strategies": [
            {
                "id": strategy.id,
                "name": strategy.name,
                "strategy_type": strategy.strategy_type.value,
                "symbol": strategy.symbol,
                "total_return": float(strategy.total_return),
                "total_trades": strategy.total_trades,
                "status": strategy.status.value
            }
            for strategy in active_strategies
        ],
        "recent_backtests": [
            {
                "id": backtest.id,
                "name": backtest.name,
                "strategy_id": backtest.strategy_id,
                "symbol": backtest.symbol,
                "status": backtest.status.value,
                "total_return": float(backtest.total_return),
                "total_trades": backtest.total_trades,
                "created_at": backtest.created_at.isoformat()
            }
            for backtest in recent_backtests
        ]
    }


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial data
        db = next(get_db())
        service = TradingStrategyService(db)
        integration_service = PaperTradingIntegrationService(db)
        
        # Get user's active strategies
        strategies = service.get_strategies(user_id, status=StrategyStatus.ACTIVE)
        
        initial_data = {
            "type": "initial_data",
            "strategies": [
                {
                    "id": strategy.id,
                    "name": strategy.name,
                    "status": strategy.status.value,
                    "total_return": float(strategy.total_return),
                    "total_trades": strategy.total_trades
                }
                for strategy in strategies
            ]
        }
        
        await manager.broadcast_to_user(initial_data, user_id)
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(30)  # Update every 30 seconds
            
            # Get updated data
            updated_strategies = service.get_strategies(user_id, status=StrategyStatus.ACTIVE)
            
            update_data = {
                "type": "update",
                "timestamp": datetime.utcnow().isoformat(),
                "strategies": [
                    {
                        "id": strategy.id,
                        "name": strategy.name,
                        "status": strategy.status.value,
                        "total_return": float(strategy.total_return),
                        "total_trades": strategy.total_trades,
                        "current_balance": float(strategy.current_balance),
                        "total_equity": float(strategy.total_equity),
                        "last_run_at": strategy.last_run_at.isoformat() if strategy.last_run_at else None
                    }
                    for strategy in updated_strategies
                ]
            }
            
            await manager.broadcast_to_user(update_data, user_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logging.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


@router.post("/strategies/{strategy_id}/simulate")
async def simulate_strategy_execution(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Simulate strategy execution (for testing)."""
    integration_service = PaperTradingIntegrationService(db)
    
    success = await integration_service.execute_strategy_live(strategy_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to execute strategy")
    
    return {"message": "Strategy execution simulated successfully"}


@router.get("/market/data/{symbol}")
async def get_market_data(
    symbol: str,
    timeframe: str = "1d",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get market data for a symbol."""
    integration_service = PaperTradingIntegrationService(db)
    
    try:
        from paper_trading.core.data_feed import DataFeed
        
        data_feed = DataFeed()
        data = data_feed.get_data(
            symbol=symbol,
            interval=timeframe,
            start_date=(datetime.now() - timedelta(days=limit)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d'),
            source='binance'
        )
        
        if data.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Convert to JSON-serializable format
        data_dict = data.reset_index().to_dict('records')
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": data_dict,
            "count": len(data_dict)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")


@router.get("/alerts/active")
async def get_active_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active alerts for the user."""
    # This would integrate with the notification system
    # For now, return empty list
    return {
        "alerts": [],
        "count": 0
    }
