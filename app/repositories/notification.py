"""Notification repository.

Data access layer for Notification model.
"""
from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationStatus, NotificationType
from app.repositories.base import BaseRepository
from app.schemas.notification import NotificationCreate, NotificationUpdate


class NotificationRepository(BaseRepository[Notification, NotificationCreate, NotificationUpdate]):
    """Repository for Notification model."""

    async def get_by_member_id(
        self,
        member_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Get notifications for a member."""
        result = await self.session.execute(
            select(Notification)
            .where(Notification.member_id == member_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_status(
        self,
        status: NotificationStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Get notifications by status."""
        result = await self.session.execute(
            select(Notification)
            .where(Notification.status == status)
            .order_by(Notification.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_pending_notifications(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Get pending notifications ready to send."""
        from datetime import datetime

        now = datetime.utcnow()
        result = await self.session.execute(
            select(Notification)
            .where(Notification.status == NotificationStatus.PENDING)
            .where(
                (Notification.scheduled_at.is_(None)) |
                (Notification.scheduled_at <= now)
            )
            .order_by(Notification.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_type(
        self,
        notification_type: NotificationType,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Get notifications by type."""
        result = await self.session.execute(
            select(Notification)
            .where(Notification.notification_type == notification_type)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_loan_id(self, loan_id: uuid.UUID) -> Sequence[Notification]:
        """Get notifications related to a loan."""
        result = await self.session.execute(
            select(Notification)
            .where(Notification.related_loan_id == loan_id)
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_gate_event_id(self, gate_event_id: uuid.UUID) -> Sequence[Notification]:
        """Get notifications related to a gate event."""
        result = await self.session.execute(
            select(Notification)
            .where(Notification.related_gate_event_id == gate_event_id)
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()
