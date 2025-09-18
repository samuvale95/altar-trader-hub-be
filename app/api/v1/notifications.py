"""
Notification API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.notification import Notification, NotificationTemplate
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationTemplateCreate,
    NotificationTemplateResponse,
    NotificationFilter,
    NotificationStats,
    PriceAlert,
    StrategyAlert
)
from app.services.notification_service import notification_service
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    filter_params: NotificationFilter = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notifications with optional filtering."""
    
    # Build query
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    # Apply filters
    if filter_params.type:
        query = query.filter(Notification.type == filter_params.type)
    
    if filter_params.status:
        query = query.filter(Notification.status == filter_params.status)
    
    if filter_params.priority:
        query = query.filter(Notification.priority == filter_params.priority)
    
    if filter_params.start_date:
        query = query.filter(Notification.created_at >= filter_params.start_date)
    
    if filter_params.end_date:
        query = query.filter(Notification.created_at <= filter_params.end_date)
    
    # Apply pagination
    notifications = query.order_by(Notification.created_at.desc()).offset(
        filter_params.offset
    ).limit(filter_params.limit).all()
    
    return notifications


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new notification."""
    
    # Create notification
    notification = Notification(
        user_id=current_user.id,
        type=notification_data.type,
        title=notification_data.title,
        message=notification_data.message,
        priority=notification_data.priority,
        recipient=notification_data.recipient,
        data=notification_data.data,
        metadata=notification_data.metadata,
        template_id=notification_data.template_id,
        scheduled_at=notification_data.scheduled_at,
        max_retries=notification_data.max_retries
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    logger.info("Notification created", notification_id=notification.id, user_id=current_user.id)
    
    return notification


@router.get("/templates", response_model=List[NotificationTemplateResponse])
def get_notification_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification templates."""
    
    templates = db.query(NotificationTemplate).filter(
        NotificationTemplate.is_active == True
    ).all()
    
    return templates


@router.post("/templates", response_model=NotificationTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_notification_template(
    template_data: NotificationTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a notification template."""
    
    # Check if template name already exists
    existing_template = db.query(NotificationTemplate).filter(
        NotificationTemplate.name == template_data.name
    ).first()
    
    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template name already exists"
        )
    
    # Create template
    template = NotificationTemplate(
        name=template_data.name,
        description=template_data.description,
        type=template_data.type,
        title_template=template_data.title_template,
        message_template=template_data.message_template,
        variables=template_data.variables,
        default_values=template_data.default_values,
        priority=template_data.priority,
        delivery_methods=template_data.delivery_methods,
        rate_limit=template_data.rate_limit,
        cooldown_period=template_data.cooldown_period
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    logger.info("Notification template created", template_id=template.id, user_id=current_user.id)
    
    return template


@router.get("/stats", response_model=NotificationStats)
def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification statistics for user."""
    
    # Get user notifications
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).all()
    
    if not notifications:
        return NotificationStats(
            total_notifications=0,
            sent_notifications=0,
            failed_notifications=0,
            pending_notifications=0,
            success_rate=0
        )
    
    # Calculate statistics
    total_notifications = len(notifications)
    sent_notifications = len([n for n in notifications if n.status == "sent"])
    failed_notifications = len([n for n in notifications if n.status == "failed"])
    pending_notifications = len([n for n in notifications if n.status == "pending"])
    
    success_rate = (sent_notifications / total_notifications * 100) if total_notifications > 0 else 0
    
    # Calculate average delivery time
    sent_notifications_with_time = [
        n for n in notifications 
        if n.status == "sent" and n.sent_at and n.created_at
    ]
    
    avg_delivery_time = None
    if sent_notifications_with_time:
        delivery_times = [
            (n.sent_at - n.created_at).total_seconds() 
            for n in sent_notifications_with_time
        ]
        avg_delivery_time = sum(delivery_times) / len(delivery_times)
    
    # Most common type
    type_counts = {}
    for notification in notifications:
        type_counts[notification.type.value] = type_counts.get(notification.type.value, 0) + 1
    
    most_common_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
    
    # Most common failure reason
    failure_reasons = [
        n.failure_reason for n in notifications 
        if n.failure_reason
    ]
    most_common_failure_reason = None
    if failure_reasons:
        reason_counts = {}
        for reason in failure_reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        most_common_failure_reason = max(reason_counts.items(), key=lambda x: x[1])[0]
    
    return NotificationStats(
        total_notifications=total_notifications,
        sent_notifications=sent_notifications,
        failed_notifications=failed_notifications,
        pending_notifications=pending_notifications,
        success_rate=success_rate,
        avg_delivery_time=avg_delivery_time,
        most_common_type=most_common_type,
        most_common_failure_reason=most_common_failure_reason
    )


@router.post("/price-alerts")
def create_price_alert(
    alert_data: PriceAlert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a price alert."""
    
    # TODO: Implement price alert creation
    # This would involve:
    # 1. Creating a price alert record
    # 2. Setting up monitoring for the symbol
    # 3. Scheduling checks for price conditions
    
    logger.info("Price alert created", user_id=current_user.id, symbol=alert_data.symbol)
    
    return {"message": "Price alert created successfully", "alert_id": "alert_123"}


@router.post("/strategy-alerts")
def create_strategy_alert(
    alert_data: StrategyAlert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a strategy alert."""
    
    # TODO: Implement strategy alert creation
    # This would involve:
    # 1. Creating a strategy alert record
    # 2. Setting up monitoring for the strategy
    # 3. Scheduling checks for alert conditions
    
    logger.info("Strategy alert created", user_id=current_user.id, strategy_id=alert_data.strategy_id)
    
    return {"message": "Strategy alert created successfully", "alert_id": "alert_456"}


@router.post("/test")
def send_test_notification(
    notification_type: str,
    current_user: User = Depends(get_current_user)
):
    """Send a test notification."""
    
    from app.models.notification import NotificationType
    
    try:
        notification_type_enum = NotificationType(notification_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid notification type: {notification_type}"
        )
    
    # Send test notification
    success = asyncio.create_task(notification_service.send_notification(
        user_id=current_user.id,
        notification_type=notification_type_enum,
        title="Test Notification",
        message="This is a test notification to verify your notification settings.",
        data={"test": True},
        priority="low"
    ))
    
    if success:
        return {"message": "Test notification sent successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )


@router.post("/retry-failed")
def retry_failed_notifications(
    current_user: User = Depends(get_current_user)
):
    """Retry failed notifications for user."""
    
    # TODO: Implement retry logic for specific user
    # This would involve filtering failed notifications by user_id
    
    retry_count = asyncio.create_task(notification_service.retry_failed_notifications())
    
    return {"message": f"Retried {retry_count} failed notifications"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification."""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    
    logger.info("Notification deleted", notification_id=notification_id, user_id=current_user.id)
    
    return {"message": "Notification deleted successfully"}


@router.put("/{notification_id}/mark-read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Update notification metadata to mark as read
    if not notification.metadata:
        notification.metadata = {}
    
    notification.metadata["read"] = True
    notification.metadata["read_at"] = datetime.utcnow().isoformat()
    
    db.commit()
    
    logger.info("Notification marked as read", notification_id=notification_id, user_id=current_user.id)
    
    return {"message": "Notification marked as read"}
