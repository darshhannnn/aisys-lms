"""Notifications API endpoints.

Email, SMS, and print notification management (FR09, AC06).
"""
from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DatabaseSession, require_librarian
from app.db.session import get_db
from app.models.notification import NotificationChannel, NotificationType
from app.services.notifications import NotificationsService
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationTemplateRequest,
    BulkNotificationRequest,
    BulkNotificationResponse,
)

log = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=NotificationResponse, summary="Create notification")
async def create_notification(
    request: NotificationCreate,
    db: DatabaseSession,
    current_user: Annotated[object, Depends(require_librarian)],
):
    """Create a new notification."""
    service = NotificationsService(db)
    notification = await service.create_notification(
        member_id=request.member_id,
        channel=request.channel,
        notification_type=request.notification_type,
        subject=request.subject,
        body=request.body,
        **{k: v for k, v in request.model_dump().items() if k not in [
            "member_id", "channel", "notification_type", "subject", "body"
        ]},
    )

    log.info(
        "notification_created",
        notification_id=str(notification.id),
        member_id=str(request.member_id),
        channel=request.channel.value,
        type=request.notification_type.value,
    )

    return notification


@router.post("/template", summary="Create notification from template")
async def create_from_template(
    request: NotificationTemplateRequest,
    db: DatabaseSession,
    current_user: Annotated[object, Depends(require_librarian)],
):
    """Create a notification from a predefined template."""
    service = NotificationsService(db)

    # Simple template rendering (in production, use proper template engine)
    context = request.context or {}
    body = f"Notification for member {request.member_id}. Context: {context}"

    notification = await service.create_notification(
        member_id=request.member_id,
        channel=NotificationChannel.EMAIL,
        notification_type=request.notification_type,
        subject=f"{request.notification_type.value.replace('_', ' ').title()}",
        body=body,
    )

    return notification


@router.post("/bulk", response_model=BulkNotificationResponse, summary="Send bulk notifications")
async def send_bulk_notifications(
    request: BulkNotificationRequest,
    db: DatabaseSession,
    current_user: Annotated[object, Depends(require_librarian)],
):
    """Send notifications to multiple members."""
    service = NotificationsService(db)

    created_count = 0
    failed_count = 0
    notification_ids = []

    for member_id in request.member_ids:
        try:
            notification = await service.create_notification(
                member_id=member_id,
                channel=request.channel,
                notification_type=request.notification_type,
                subject=request.subject,
                body=request.body_template,
                scheduled_at=request.scheduled_at,
                metadata=request.context,
            )
            created_count += 1
            notification_ids.append(notification.id)
        except Exception as e:
            failed_count += 1
            log.error("bulk_notification_failed", member_id=str(member_id), error=str(e))

    log.info(
        "bulk_notifications_sent",
        total_requested=len(request.member_ids),
        created=created_count,
        failed=failed_count,
    )

    return BulkNotificationResponse(
        total_requested=len(request.member_ids),
        created_count=created_count,
        failed_count=failed_count,
        notification_ids=notification_ids,
    )


@router.get("/member/{member_id}", summary="Get member notifications")
async def get_member_notifications(
    member_id: str,
    limit: int = 50,
    db: DatabaseSession,
    current_user: Annotated[object, Depends(require_librarian)],
):
    """Get notifications for a specific member."""
    from uuid import UUID

    service = NotificationsService(db)
    notifications = await service.get_member_notifications(UUID(member_id), limit=limit)
    return notifications


@router.post("/send-overdue-reminders", summary="Send overdue reminders")
async def send_overdue_reminders(
    db: DatabaseSession,
    current_user: Annotated[object, Depends(require_librarian)],
):
    """Send reminder notifications for items due soon."""
    service = NotificationsService(db)
    count = await service.send_overdue_reminders()

    log.info("overdue_reminders_sent", count=count)

    return {"count": count, "message": f"Sent {count} overdue reminders"}


@router.post("/send-overdue-notices", summary="Send overdue notices")
async def send_overdue_notices(
    db: DatabaseSession,
    current_user: Annotated[object, Depends(require_librarian)],
):
    """Send overdue notices for items past due date."""
    service = NotificationsService(db)
    count = await service.send_overdue_notices()

    log.info("overdue_notices_sent", count=count)

    return {"count": count, "message": f"Sent {count} overdue notices"}
