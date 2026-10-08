"""Notifications service.

Business logic for email, SMS, and print notifications (FR09, AC06).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationStatus, NotificationType, NotificationChannel
from app.repositories.notification import NotificationRepository


class NotificationsService:
    """Notifications business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_repo = NotificationRepository(Notification, session)

    async def create_notification(
        self,
        member_id: uuid.UUID | None,
        channel: NotificationChannel,
        notification_type: NotificationType,
        subject: str,
        body: str,
        **kwargs,
    ) -> Notification:
        """Create a new notification."""
        from app.schemas.notification import NotificationCreate

        notification_data = NotificationCreate(
            member_id=member_id,
            channel=channel,
            notification_type=notification_type,
            subject=subject,
            body=body,
            **kwargs,
        )
        return await self.notification_repo.create(notification_data)

    async def send_overdue_reminders(self) -> int:
        """Send overdue loan reminders."""
        from app.models.circulation import Loan
        from datetime import date, timedelta

        # Find loans due in 3 days
        due_date = date.today() + timedelta(days=3)
        result = await self.session.execute(
            select(Loan)
            .where(Loan.due_date == due_date)
            .where(Loan.returned_at.is_(None))
        )
        loans = result.scalars().all()

        count = 0
        for loan in loans:
            notification = await self.create_notification(
                member_id=loan.member_id,
                channel=NotificationChannel.EMAIL,
                notification_type=NotificationType.LOAN_DUE_REMINDER,
                subject="Library Item Due Soon",
                body=f"Your borrowed item is due on {loan.due_date}. Please return or renew.",
                related_loan_id=loan.id,
            )
            count += 1

        return count

    async def send_overdue_notices(self) -> int:
        """Send overdue notices for items past due date."""
        from app.models.circulation import Loan
        from datetime import date

        # Find overdue loans
        today = date.today()
        result = await self.session.execute(
            select(Loan)
            .where(Loan.due_date < today)
            .where(Loan.returned_at.is_(None))
        )
        loans = result.scalars().all()

        count = 0
        for loan in loans:
            notification = await self.create_notification(
                member_id=loan.member_id,
                channel=NotificationChannel.EMAIL,
                notification_type=NotificationType.OVERDUE_NOTICE,
                subject="Library Item Overdue",
                body=f"Your borrowed item was due on {loan.due_date} and is now overdue.",
                related_loan_id=loan.id,
            )
            count += 1

        return count

    async def get_pending_notifications(self) -> list[Notification]:
        """Get notifications ready to be sent."""
        return list(await self.notification_repo.get_pending_notifications())

    async def mark_as_sent(self, notification_id: uuid.UUID) -> Notification:
        """Mark notification as sent."""
        notification = await self.notification_repo.get(notification_id)
        if not notification:
            raise ValueError("Notification not found")

        from app.schemas.notification import NotificationUpdate

        return await self.notification_repo.update(
            notification,
            NotificationUpdate(
                status=NotificationStatus.SENT,
                sent_at=datetime.now(timezone.utc),
            ),
        )

    async def mark_as_failed(
        self,
        notification_id: uuid.UUID,
        error_message: str,
    ) -> Notification:
        """Mark notification as failed."""
        notification = await self.notification_repo.get(notification_id)
        if not notification:
            raise ValueError("Notification not found")

        from app.schemas.notification import NotificationUpdate

        return await self.notification_repo.update(
            notification,
            NotificationUpdate(
                status=NotificationStatus.FAILED,
                error_message=error_message,
            ),
        )

    async def get_member_notifications(
        self,
        member_id: uuid.UUID,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications for a member."""
        return list(await self.notification_repo.get_by_member_id(member_id, skip=0, limit=limit))
