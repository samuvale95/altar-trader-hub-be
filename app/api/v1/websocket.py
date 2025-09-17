"""
WebSocket endpoints for real-time updates.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.core.logging import get_logger
import json
import asyncio
from datetime import datetime

router = APIRouter()
logger = get_logger(__name__)

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        # Dictionary to store active connections by user_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Dictionary to store connection subscriptions
        self.subscriptions: Dict[WebSocket, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept a WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.subscriptions[websocket] = []
        
        logger.info("WebSocket connected", user_id=user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        
        logger.info("WebSocket disconnected", user_id=user_id)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error("Failed to send message", error=str(e))
    
    async def send_to_user(self, message: str, user_id: int):
        """Send a message to all connections of a user."""
        if user_id in self.active_connections:
            for websocket in self.active_connections[user_id]:
                await self.send_personal_message(message, websocket)
    
    async def broadcast_to_subscribers(self, message: str, subscription_type: str):
        """Broadcast a message to all subscribers of a specific type."""
        for websocket, subscriptions in self.subscriptions.items():
            if subscription_type in subscriptions:
                await self.send_personal_message(message, websocket)
    
    def subscribe(self, websocket: WebSocket, subscription_type: str):
        """Subscribe a WebSocket to a specific type of updates."""
        if websocket in self.subscriptions:
            if subscription_type not in self.subscriptions[websocket]:
                self.subscriptions[websocket].append(subscription_type)
                logger.info("WebSocket subscribed", subscription_type=subscription_type)
    
    def unsubscribe(self, websocket: WebSocket, subscription_type: str):
        """Unsubscribe a WebSocket from a specific type of updates."""
        if websocket in self.subscriptions:
            if subscription_type in self.subscriptions[websocket]:
                self.subscriptions[websocket].remove(subscription_type)
                logger.info("WebSocket unsubscribed", subscription_type=subscription_type)

# Global connection manager
manager = ConnectionManager()


@router.websocket("/portfolio")
async def websocket_portfolio(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for portfolio updates."""
    
    # Verify token and get user
    try:
        from app.core.security import verify_token
        user_id = verify_token(token, "access")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
    except Exception as e:
        logger.error("WebSocket authentication failed", error=str(e))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect WebSocket
    await manager.connect(websocket, user_id)
    
    try:
        # Subscribe to portfolio updates
        manager.subscribe(websocket, "portfolio")
        
        # Send initial portfolio data
        from app.api.v1.portfolio import get_portfolio_overview
        overview = get_portfolio_overview(user, db)
        
        initial_message = {
            "type": "portfolio_update",
            "data": overview.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(
            json.dumps(initial_message), 
            websocket
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle subscription changes
                if message.get("type") == "subscribe":
                    subscription_type = message.get("subscription_type")
                    if subscription_type:
                        manager.subscribe(websocket, subscription_type)
                        
                elif message.get("type") == "unsubscribe":
                    subscription_type = message.get("subscription_type")
                    if subscription_type:
                        manager.unsubscribe(websocket, subscription_type)
                
                # Send acknowledgment
                ack_message = {
                    "type": "ack",
                    "message": "Message received",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_personal_message(
                    json.dumps(ack_message), 
                    websocket
                )
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("WebSocket error", error=str(e))
                break
                
    finally:
        manager.disconnect(websocket, user_id)


@router.websocket("/orders")
async def websocket_orders(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for order updates."""
    
    # Verify token and get user
    try:
        from app.core.security import verify_token
        user_id = verify_token(token, "access")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
    except Exception as e:
        logger.error("WebSocket authentication failed", error=str(e))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect WebSocket
    await manager.connect(websocket, user_id)
    
    try:
        # Subscribe to order updates
        manager.subscribe(websocket, "orders")
        
        # Send initial orders data
        from app.api.v1.orders import get_orders
        from app.schemas.order import OrderFilter
        
        orders = get_orders(OrderFilter(), user, db)
        
        initial_message = {
            "type": "orders_update",
            "data": [order.dict() for order in orders],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(
            json.dumps(initial_message), 
            websocket
        )
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle subscription changes
                if message.get("type") == "subscribe":
                    subscription_type = message.get("subscription_type")
                    if subscription_type:
                        manager.subscribe(websocket, subscription_type)
                        
                elif message.get("type") == "unsubscribe":
                    subscription_type = message.get("subscription_type")
                    if subscription_type:
                        manager.unsubscribe(websocket, subscription_type)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("WebSocket error", error=str(e))
                break
                
    finally:
        manager.disconnect(websocket, user_id)


@router.websocket("/market-data")
async def websocket_market_data(
    websocket: WebSocket,
    symbols: str = None
):
    """WebSocket endpoint for market data updates."""
    
    # Connect WebSocket (no authentication required for market data)
    await manager.connect(websocket, 0)  # Use 0 for anonymous connections
    
    try:
        # Subscribe to market data updates
        manager.subscribe(websocket, "market_data")
        
        # Parse symbols
        symbol_list = symbols.split(',') if symbols else []
        
        # Send initial market data
        initial_message = {
            "type": "market_data_update",
            "data": {
                "symbols": symbol_list,
                "message": "Connected to market data stream"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(
            json.dumps(initial_message), 
            websocket
        )
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle subscription changes
                if message.get("type") == "subscribe":
                    subscription_type = message.get("subscription_type")
                    if subscription_type:
                        manager.subscribe(websocket, subscription_type)
                        
                elif message.get("type") == "unsubscribe":
                    subscription_type = message.get("subscription_type")
                    if subscription_type:
                        manager.unsubscribe(websocket, subscription_type)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("WebSocket error", error=str(e))
                break
                
    finally:
        manager.disconnect(websocket, 0)


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for notifications."""
    
    # Verify token and get user
    try:
        from app.core.security import verify_token
        user_id = verify_token(token, "access")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
    except Exception as e:
        logger.error("WebSocket authentication failed", error=str(e))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect WebSocket
    await manager.connect(websocket, user_id)
    
    try:
        # Subscribe to notifications
        manager.subscribe(websocket, "notifications")
        
        # Send initial notification
        initial_message = {
            "type": "notification",
            "data": {
                "message": "Connected to notifications stream",
                "user_id": user_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(
            json.dumps(initial_message), 
            websocket
        )
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle subscription changes
                if message.get("type") == "subscribe":
                    subscription_type = message.get("subscription_type")
                    if subscription_type:
                        manager.subscribe(websocket, subscription_type)
                        
                elif message.get("type") == "unsubscribe":
                    subscription_type = message.get("subscription_type")
                    if subscription_type:
                        manager.unsubscribe(websocket, subscription_type)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("WebSocket error", error=str(e))
                break
                
    finally:
        manager.disconnect(websocket, user_id)


# Utility functions for sending updates
async def send_portfolio_update(user_id: int, data: Dict[str, Any]):
    """Send portfolio update to user."""
    message = {
        "type": "portfolio_update",
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_to_user(json.dumps(message), user_id)


async def send_order_update(user_id: int, data: Dict[str, Any]):
    """Send order update to user."""
    message = {
        "type": "order_update",
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_to_user(json.dumps(message), user_id)


async def send_market_data_update(symbol: str, data: Dict[str, Any]):
    """Send market data update to all subscribers."""
    message = {
        "type": "market_data_update",
        "data": {
            "symbol": symbol,
            **data
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast_to_subscribers(json.dumps(message), "market_data")


async def send_notification(user_id: int, data: Dict[str, Any]):
    """Send notification to user."""
    message = {
        "type": "notification",
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_to_user(json.dumps(message), user_id)
