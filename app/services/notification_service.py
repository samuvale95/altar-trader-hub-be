"""
Notification service for sending various types of notifications.
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.notification import Notification, NotificationTemplate, NotificationType, NotificationStatus
from app.models.user import User
from app.api.v1.websocket import send_notification
from app.core.config import settings
import aiosmtplib
import httpx

logger = get_logger(__name__)


class NotificationService:
    """Service for handling notifications."""
    
    def __init__(self):
        self.smtp_config = {
            'host': settings.smtp_host,
            'port': settings.smtp_port,
            'username': settings.smtp_username,
            'password': settings.smtp_password,
            'use_tls': settings.smtp_use_tls
        }
        self.telegram_config = {
            'bot_token': settings.telegram_bot_token,
            'chat_id': settings.telegram_chat_id
        }
    
    async def send_notification(
        self, 
        user_id: int, 
        notification_type: NotificationType,
        title: str, 
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "medium"
    ) -> bool:
        """Send a notification to a user."""
        
        db = SessionLocal()
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error("User not found", user_id=user_id)
                return False
            
            # Check user preferences
            if not self._should_send_notification(user, notification_type):
                logger.info("Notification skipped due to user preferences", user_id=user_id, type=notification_type)
                return True
            
            # Create notification record
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                data=data or {},
                priority=priority,
                recipient=self._get_recipient(user, notification_type)
            )
            
            db.add(notification)
            db.commit()
            
            # Send notification based on type
            success = False
            
            if notification_type == NotificationType.EMAIL:
                success = await self._send_email_notification(notification, user)
            elif notification_type == NotificationType.TELEGRAM:
                success = await self._send_telegram_notification(notification, user)
            elif notification_type == NotificationType.WEBSOCKET:
                success = await self._send_websocket_notification(notification, user)
            elif notification_type == NotificationType.PUSH:
                success = await self._send_push_notification(notification, user)
            
            # Update notification status
            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = NotificationStatus.FAILED
                notification.failed_at = datetime.utcnow()
                notification.failure_reason = "Failed to send notification"
            
            db.commit()
            
            logger.info("Notification sent", 
                       notification_id=notification.id, 
                       user_id=user_id, 
                       type=notification_type, 
                       success=success)
            
            return success
            
        except Exception as e:
            logger.error("Failed to send notification", user_id=user_id, error=str(e))
            db.rollback()
            return False
        finally:
            db.close()
    
    def _should_send_notification(self, user: User, notification_type: NotificationType) -> bool:
        """Check if notification should be sent based on user preferences."""
        
        if not user.preferences:
            return True
        
        prefs = user.preferences
        
        if notification_type == NotificationType.EMAIL:
            return prefs.email_notifications
        elif notification_type == NotificationType.PUSH:
            return prefs.push_notifications
        elif notification_type == NotificationType.TELEGRAM:
            return prefs.telegram_notifications
        elif notification_type == NotificationType.WEBSOCKET:
            return True  # Always send WebSocket notifications
        
        return True
    
    def _get_recipient(self, user: User, notification_type: NotificationType) -> Optional[str]:
        """Get recipient address for notification type."""
        
        if notification_type == NotificationType.EMAIL:
            return user.email
        elif notification_type == NotificationType.TELEGRAM:
            return user.preferences.telegram_chat_id if user.preferences else None
        elif notification_type == NotificationType.PUSH:
            return user.email  # Use email as push notification target
        elif notification_type == NotificationType.WEBSOCKET:
            return str(user.id)  # Use user ID for WebSocket
        
        return None
    
    async def _send_email_notification(self, notification: Notification, user: User) -> bool:
        """Send email notification."""
        
        try:
            if not self.smtp_config['host']:
                logger.warning("SMTP not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['username']
            msg['To'] = notification.recipient
            msg['Subject'] = notification.title
            
            # Add body
            msg.attach(MIMEText(notification.message, 'html'))
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_config['host'],
                port=self.smtp_config['port'],
                username=self.smtp_config['username'],
                password=self.smtp_config['password'],
                use_tls=self.smtp_config['use_tls']
            )
            
            logger.info("Email notification sent", notification_id=notification.id)
            return True
            
        except Exception as e:
            logger.error("Failed to send email notification", notification_id=notification.id, error=str(e))
            return False
    
    async def _send_telegram_notification(self, notification: Notification, user: User) -> bool:
        """Send Telegram notification."""
        
        try:
            if not self.telegram_config['bot_token'] or not notification.recipient:
                logger.warning("Telegram not configured or no chat ID")
                return False
            
            # Format message
            message = f"*{notification.title}*\n\n{notification.message}"
            
            # Send to Telegram
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage",
                    json={
                        'chat_id': notification.recipient,
                        'text': message,
                        'parse_mode': 'Markdown'
                    }
                )
                
                if response.status_code == 200:
                    logger.info("Telegram notification sent", notification_id=notification.id)
                    return True
                else:
                    logger.error("Telegram API error", 
                               notification_id=notification.id, 
                               status_code=response.status_code,
                               response=response.text)
                    return False
            
        except Exception as e:
            logger.error("Failed to send Telegram notification", notification_id=notification.id, error=str(e))
            return False
    
    async def _send_websocket_notification(self, notification: Notification, user: User) -> bool:
        """Send WebSocket notification."""
        
        try:
            await send_notification(user.id, {
                'id': notification.id,
                'type': notification.type.value,
                'title': notification.title,
                'message': notification.message,
                'data': notification.data,
                'priority': notification.priority,
                'timestamp': notification.created_at.isoformat()
            })
            
            logger.info("WebSocket notification sent", notification_id=notification.id)
            return True
            
        except Exception as e:
            logger.error("Failed to send WebSocket notification", notification_id=notification.id, error=str(e))
            return False
    
    async def _send_push_notification(self, notification: Notification, user: User) -> bool:
        """Send push notification (placeholder for FCM integration)."""
        
        try:
            # TODO: Implement FCM push notification
            # This would involve:
            # 1. Getting user's FCM token
            # 2. Sending notification via FCM API
            # 3. Handling responses and errors
            
            logger.info("Push notification sent (placeholder)", notification_id=notification.id)
            return True
            
        except Exception as e:
            logger.error("Failed to send push notification", notification_id=notification.id, error=str(e))
            return False
    
    async def send_trade_notification(
        self, 
        user_id: int, 
        trade_data: Dict[str, Any]
    ) -> bool:
        """Send trade execution notification."""
        
        title = f"Trade Executed - {trade_data['symbol']}"
        message = f"""
        <h3>Trade Details</h3>
        <p><strong>Symbol:</strong> {trade_data['symbol']}</p>
        <p><strong>Side:</strong> {trade_data['side']}</p>
        <p><strong>Quantity:</strong> {trade_data['quantity']}</p>
        <p><strong>Price:</strong> ${trade_data['price']}</p>
        <p><strong>P&L:</strong> ${trade_data.get('pnl', 0)}</p>
        <p><strong>Time:</strong> {trade_data['timestamp']}</p>
        """
        
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.EMAIL,
            title=title,
            message=message,
            data=trade_data,
            priority="high"
        )
    
    async def send_strategy_signal_notification(
        self, 
        user_id: int, 
        signal_data: Dict[str, Any]
    ) -> bool:
        """Send strategy signal notification."""
        
        title = f"Strategy Signal - {signal_data['strategy_name']}"
        message = f"""
        <h3>Signal Details</h3>
        <p><strong>Strategy:</strong> {signal_data['strategy_name']}</p>
        <p><strong>Symbol:</strong> {signal_data['symbol']}</p>
        <p><strong>Signal:</strong> {signal_data['signal_type']}</p>
        <p><strong>Price:</strong> ${signal_data['price']}</p>
        <p><strong>Confidence:</strong> {signal_data['confidence']}%</p>
        <p><strong>Reasoning:</strong> {signal_data.get('reasoning', 'N/A')}</p>
        """
        
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.EMAIL,
            title=title,
            message=message,
            data=signal_data,
            priority="medium"
        )
    
    async def send_price_alert_notification(
        self, 
        user_id: int, 
        alert_data: Dict[str, Any]
    ) -> bool:
        """Send price alert notification."""
        
        title = f"Price Alert - {alert_data['symbol']}"
        message = f"""
        <h3>Price Alert Triggered</h3>
        <p><strong>Symbol:</strong> {alert_data['symbol']}</p>
        <p><strong>Current Price:</strong> ${alert_data['current_price']}</p>
        <p><strong>Target Price:</strong> ${alert_data['target_price']}</p>
        <p><strong>Condition:</strong> {alert_data['condition']}</p>
        <p><strong>Time:</strong> {alert_data['timestamp']}</p>
        """
        
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.EMAIL,
            title=title,
            message=message,
            data=alert_data,
            priority="high"
        )
    
    async def send_system_alert_notification(
        self, 
        user_id: int, 
        alert_data: Dict[str, Any]
    ) -> bool:
        """Send system alert notification."""
        
        title = f"System Alert - {alert_data['alert_type']}"
        message = f"""
        <h3>System Alert</h3>
        <p><strong>Type:</strong> {alert_data['alert_type']}</p>
        <p><strong>Message:</strong> {alert_data['message']}</p>
        <p><strong>Severity:</strong> {alert_data['severity']}</p>
        <p><strong>Time:</strong> {alert_data['timestamp']}</p>
        """
        
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.EMAIL,
            title=title,
            message=message,
            data=alert_data,
            priority=alert_data.get('severity', 'medium')
        )
    
    async def retry_failed_notifications(self) -> int:
        """Retry failed notifications."""
        
        db = SessionLocal()
        retry_count = 0
        
        try:
            # Get failed notifications that can be retried
            failed_notifications = db.query(Notification).filter(
                Notification.status == NotificationStatus.FAILED,
                Notification.retry_count < Notification.max_retries,
                Notification.created_at > datetime.utcnow() - timedelta(hours=24)
            ).all()
            
            for notification in failed_notifications:
                try:
                    # Get user
                    user = db.query(User).filter(User.id == notification.user_id).first()
                    if not user:
                        continue
                    
                    # Retry sending
                    success = False
                    
                    if notification.type == NotificationType.EMAIL:
                        success = await self._send_email_notification(notification, user)
                    elif notification.type == NotificationType.TELEGRAM:
                        success = await self._send_telegram_notification(notification, user)
                    elif notification.type == NotificationType.WEBSOCKET:
                        success = await self._send_websocket_notification(notification, user)
                    elif notification.type == NotificationType.PUSH:
                        success = await self._send_push_notification(notification, user)
                    
                    # Update notification
                    notification.retry_count += 1
                    
                    if success:
                        notification.status = NotificationStatus.SENT
                        notification.sent_at = datetime.utcnow()
                        retry_count += 1
                    else:
                        if notification.retry_count >= notification.max_retries:
                            notification.status = NotificationStatus.FAILED
                            notification.failed_at = datetime.utcnow()
                    
                    db.commit()
                    
                except Exception as e:
                    logger.error("Failed to retry notification", 
                               notification_id=notification.id, 
                               error=str(e))
                    continue
            
            logger.info("Retried failed notifications", count=retry_count)
            return retry_count
            
        except Exception as e:
            logger.error("Failed to retry notifications", error=str(e))
            db.rollback()
            return 0
        finally:
            db.close()


# Global notification service instance
notification_service = NotificationService()
