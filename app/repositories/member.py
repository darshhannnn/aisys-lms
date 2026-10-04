"""Member repository.

Data access layer for Member model.
"""
from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member, MemberStatus, MemberCategory
from app.repositories.base import BaseRepository
from app.schemas.member import MemberCreate, MemberUpdate


class MemberRepository(BaseRepository[Member, MemberCreate, MemberUpdate]):
    """Repository for Member model."""

    async def get_by_member_number(self, member_number: str) -> Optional[Member]:
        """Get member by member number."""
        return await self.get_by_field("member_number", member_number)

    async def get_by_patron_card_barcode(self, barcode: str) -> Optional[Member]:
        """Get member by patron card barcode."""
        return await self.get_by_field("patron_card_barcode", barcode)

    async def get_by_source_id(self, source_system: str, source_id: str) -> Optional[Member]:
        """Get member by source system and source ID (for migration)."""
        result = await self.session.execute(
            select(Member)
            .where(Member.source_system == source_system)
            .where(Member.source_id == source_id)
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Member]:
        """Search members by name, member number, or email."""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(Member)
            .where(
                or_(
                    Member.full_name.ilike(search_pattern),
                    Member.member_number.ilike(search_pattern),
                    Member.email.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_status(
        self,
        status: MemberStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Member]:
        """Get members by status."""
        result = await self.session.execute(
            select(Member)
            .where(Member.status == status)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_category(
        self,
        category: MemberCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Member]:
        """Get members by category."""
        result = await self.session.execute(
            select(Member)
            .where(Member.category == category)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_blocked_members(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Member]:
        """Get blocked members (FR04)."""
        return await self.get_by_status(MemberStatus.BLOCKED, skip, limit)

    async def get_active_members(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Member]:
        """Get active members only."""
        return await self.get_by_status(MemberStatus.ACTIVE, skip, limit)

    async def get_with_outstanding_fines(
        self,
        min_amount: float = 0.01,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Member]:
        """Get members with outstanding fines above threshold."""
        result = await self.session.execute(
            select(Member)
            .where(Member.outstanding_fine >= min_amount)
            .order_by(Member.outstanding_fine.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
