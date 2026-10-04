"""Catalogue service.

Business logic for bibliographic records and items.
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalogue import BibliographicRecord, Item
from app.repositories.catalogue import BibliographicRecordRepository, ItemRepository


class CatalogueService:
    """Catalogue business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.record_repo = BibliographicRecordRepository(BibliographicRecord, session)
        self.item_repo = ItemRepository(Item, session)

    async def create_bibliographic_record(
        self,
        title: str,
        author: str,
        **kwargs,
    ) -> BibliographicRecord:
        """Create a new bibliographic record."""
        from app.schemas.catalogue import BibliographicRecordCreate

        record_data = BibliographicRecordCreate(
            title=title,
            author=author,
            **kwargs,
        )
        return await self.record_repo.create(record_data)

    async def search_records(
        self,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[BibliographicRecord]:
        """Search bibliographic records (FR02)."""
        return list(await self.record_repo.search(query, skip, limit))

    async def get_record_with_items(
        self,
        record_id: uuid.UUID,
    ) -> BibliographicRecord | None:
        """Get bibliographic record with item count."""
        return await self.record_repo.get_with_item_count(record_id)

    async def create_item(
        self,
        barcode: str,
        bibliographic_record_id: uuid.UUID,
        **kwargs,
    ) -> Item:
        """Create a new item."""
        from app.schemas.catalogue import ItemCreate

        item_data = ItemCreate(
            barcode=barcode,
            bibliographic_record_id=bibliographic_record_id,
            **kwargs,
        )
        return await self.item_repo.create(item_data)

    async def get_item_by_barcode(self, barcode: str) -> Item | None:
        """Get item by barcode."""
        return await self.item_repo.get_by_barcode(barcode)

    async def get_items_by_record(
        self,
        record_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Item]:
        """Get all items for a bibliographic record."""
        return list(await self.item_repo.get_by_record_id(record_id, skip, limit))

    async def update_item_status(
        self,
        item_id: uuid.UUID,
        status: str,
    ) -> Item:
        """Update item status."""
        item = await self.item_repo.get(item_id)
        if not item:
            raise ValueError("Item not found")
        from app.schemas.catalogue import ItemUpdate

        return await self.item_repo.update(item, ItemUpdate(status=status))
