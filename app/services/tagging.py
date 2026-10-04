"""RFID tagging service.

Business logic for RFID tag association and management (FR05, AC02).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rfid import RfidTag
from app.models.catalogue import Item
from app.repositories.rfid import RfidTagRepository
from app.repositories.catalogue import ItemRepository


class TaggingService:
    """RFID tagging business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tag_repo = RfidTagRepository(RfidTag, session)
        self.item_repo = ItemRepository(Item, session)

    async def create_tag(
        self,
        tag_uid: str,
        tag_type: str = "item",
        item_id: uuid.UUID | None = None,
    ) -> RfidTag:
        """Create a new RFID tag."""
        from app.schemas.rfid import RfidTagCreate

        tag_data = RfidTagCreate(
            tag_uid=tag_uid,
            tag_type=tag_type,
            item_id=item_id,
        )
        return await self.tag_repo.create(tag_data)

    async def associate_tag_with_item(
        self,
        tag_uid: str,
        item_id: uuid.UUID,
    ) -> tuple[RfidTag, Item]:
        """Associate an RFID tag with an item (FR05, AC02)."""
        # Get or create tag
        tag = await self.tag_repo.get_by_tag_uid(tag_uid)
        if not tag:
            tag = await self.create_tag(tag_uid, "item", item_id)
        else:
            # Update existing tag
            from app.schemas.rfid import RfidTagUpdate

            tag = await self.tag_repo.update(tag, RfidTagUpdate(item_id=item_id))

        # Get item
        item = await self.item_repo.get(item_id)
        if not item:
            raise ValueError("Item not found")

        # Update item with RFID tag reference
        item.rfid_tag_id = tag.id
        item.encoded_at = datetime.utcnow()
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)

        return tag, item

    async def dissociate_tag_from_item(
        self,
        tag_uid: str,
    ) -> RfidTag:
        """Remove RFID tag association from item."""
        tag = await self.tag_repo.get_by_tag_uid(tag_uid)
        if not tag:
            raise ValueError("Tag not found")

        if tag.item_id:
            item = await self.item_repo.get(tag.item_id)
            if item:
                item.rfid_tag_id = None
                self.session.add(item)

        from app.schemas.rfid import RfidTagUpdate

        updated_tag = await self.tag_repo.update(tag, RfidTagUpdate(item_id=None))
        await self.session.flush()

        return updated_tag

    async def get_item_by_tag(self, tag_uid: str) -> Item | None:
        """Get item by RFID tag UID."""
        tag = await self.tag_repo.get_by_tag_uid(tag_uid)
        if not tag or not tag.item_id:
            return None
        return await self.item_repo.get(tag.item_id)

    async def get_tag_by_item(self, item_id: uuid.UUID) -> RfidTag | None:
        """Get RFID tag for an item."""
        return await self.tag_repo.get_by_item_id(item_id)
