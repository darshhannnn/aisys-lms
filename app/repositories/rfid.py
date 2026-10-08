"""RFID repository.

Data access layer for RfidTag and GateEvent models.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rfid import RfidTag, GateEvent
from app.repositories.base import BaseRepository
from app.schemas.rfid import RfidTagCreate, RfidTagUpdate


class RfidTagRepository(BaseRepository[RfidTag, RfidTagCreate, RfidTagUpdate]):
    """Repository for RfidTag model."""

    async def get_by_tag_uid(self, tag_uid: str) -> Optional[RfidTag]:
        """Get RFID tag by UID."""
        return await self.get_by_field("tag_uid", tag_uid)

    async def get_by_item_id(self, item_id: uuid.UUID) -> Optional[RfidTag]:
        """Get RFID tag by item ID."""
        return await self.get_by_field("item_id", item_id)

    async def get_active_tags(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[RfidTag]:
        """Get active RFID tags only."""
        result = await self.session.execute(
            select(RfidTag)
            .where(RfidTag.status == "active")
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_unassigned_tags(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[RfidTag]:
        """Get RFID tags not assigned to any item."""
        result = await self.session.execute(
            select(RfidTag)
            .where(RfidTag.item_id.is_(None))
            .where(RfidTag.status == "active")
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_tag_uids(self, tag_uids: list[str]) -> Sequence[RfidTag]:
        """Get multiple RFID tags by their UIDs."""
        result = await self.session.execute(
            select(RfidTag).where(RfidTag.tag_uid.in_(tag_uids))
        )
        return result.scalars().all()


class GateEventRepository:
    """Repository for GateEvent model (simple class without generic base)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[GateEvent]:
        """Get gate event by ID."""
        result = await self.session.execute(
            select(GateEvent).where(GateEvent.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_gate_id(
        self,
        gate_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[GateEvent]:
        """Get gate events by gate ID."""
        result = await self.session.execute(
            select(GateEvent)
            .where(GateEvent.gate_id == gate_id)
            .order_by(GateEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_alerts(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[GateEvent]:
        """Get gate events that are alerts."""
        result = await self.session.execute(
            select(GateEvent)
            .where(GateEvent.is_alert == True)  # noqa: E712
            .order_by(GateEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_date_range(
        self,
        start_time: datetime,
        end_time: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[GateEvent]:
        """Get gate events within a date range."""
        result = await self.session.execute(
            select(GateEvent)
            .where(GateEvent.created_at >= start_time)
            .where(GateEvent.created_at <= end_time)
            .order_by(GateEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, **kwargs) -> GateEvent:
        """Create a new gate event."""
        db_obj = GateEvent(**kwargs)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: GateEvent, **kwargs) -> GateEvent:
        """Update an existing gate event."""
        for field, value in kwargs.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj
