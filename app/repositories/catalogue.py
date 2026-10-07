"""Catalogue repository.

Data access layer for BibliographicRecord and Item models.
"""
from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalogue import BibliographicRecord, Item
from app.repositories.base import BaseRepository
from app.schemas.catalogue import (
    BibliographicRecordCreate,
    BibliographicRecordUpdate,
    ItemCreate,
    ItemUpdate,
)


class BibliographicRecordRepository(
    BaseRepository[BibliographicRecord, BibliographicRecordCreate, BibliographicRecordUpdate]
):
    """Repository for BibliographicRecord model."""

    async def get_by_isbn(self, isbn: str) -> Optional[BibliographicRecord]:
        """Get bibliographic record by ISBN."""
        return await self.get_by_field("isbn", isbn)

    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[BibliographicRecord]:
        """Full-text search for bibliographic records (FR02)."""
        # SQLite LIKE-based search (fallback for offline environment)
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(BibliographicRecord)
            .where(
                or_(
                    BibliographicRecord.title.ilike(search_pattern),
                    BibliographicRecord.author.ilike(search_pattern),
                    BibliographicRecord.subject.ilike(search_pattern),
                    BibliographicRecord.isbn.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_with_item_count(self, id: uuid.UUID) -> Optional[BibliographicRecord]:
        """Get bibliographic record with item count."""
        from sqlalchemy import func

        result = await self.session.execute(
            select(
                BibliographicRecord,
                func.count(Item.id).label("item_count"),
            )
            .outerjoin(Item, Item.bibliographic_record_id == BibliographicRecord.id)
            .where(BibliographicRecord.id == id)
            .group_by(BibliographicRecord.id)
        )
        row = result.first()
        if row:
            record, item_count = row
            # Set the derived attribute
            record.item_count = item_count  # type: ignore
            return record
        return None


class ItemRepository(BaseRepository[Item, ItemCreate, ItemUpdate]):
    """Repository for Item model."""

    async def get_by_barcode(self, barcode: str) -> Optional[Item]:
        """Get item by barcode."""
        return await self.get_by_field("barcode", barcode)

    async def get_by_record_id(
        self,
        bibliographic_record_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Item]:
        """Get items by bibliographic record ID."""
        result = await self.session.execute(
            select(Item)
            .where(Item.bibliographic_record_id == bibliographic_record_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_location(
        self,
        location: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Item]:
        """Get items by shelf location."""
        # Join with bibliographic record to get shelf_location
        from sqlalchemy import and_
        result = await self.session.execute(
            select(Item)
            .join(BibliographicRecord, Item.bibliographic_record_id == BibliographicRecord.id)
            .where(BibliographicRecord.shelf_location == location)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_available_items(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Item]:
        """Get available items only."""
        result = await self.session.execute(
            select(Item)
            .where(Item.status == "available")
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_rfid_tag_id(self, rfid_tag_id: uuid.UUID) -> Optional[Item]:
        """Get item by RFID tag ID."""
        from app.models.rfid import RfidTag
        result = await self.session.execute(
            select(Item).where(Item.id == RfidTag.item_id).where(RfidTag.id == rfid_tag_id)
        )
        return result.scalar_one_or_none()
