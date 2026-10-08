"""Inventory service.

Business logic for shelf inventory using handheld RFID readers (FR06, AC05).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rfid import RfidTag
from app.models.catalogue import Item
from app.repositories.rfid import RfidTagRepository
from app.repositories.catalogue import ItemRepository


class InventoryDiscrepancy:
    """Represents an inventory mismatch."""

    def __init__(
        self,
        tag_uid: str,
        expected_location: str | None,
        actual_location: str | None,
        status: str,
    ):
        self.tag_uid = tag_uid
        self.expected_location = expected_location
        self.actual_location = actual_location
        self.status = status  # missing, misplaced, found


class InventoryService:
    """Inventory business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tag_repo = RfidTagRepository(RfidTag, session)
        self.item_repo = ItemRepository(Item, session)

    async def scan_inventory(
        self,
        location: str,
        scanned_tags: list[str],
        scanner_id: str | None = None,
    ) -> dict[str, Any]:
        """Perform inventory scan at a location (FR06, AC05)."""
        scan_id = uuid.uuid4()

        # Get all tags that should be at this location
        expected_items = await self.item_repo.get_by_location(location)
        expected_tag_uids = []
        for item in expected_items:
            tag = await self.tag_repo.get_by_item_id(item.id)
            if tag:
                expected_tag_uids.append(tag.tag_uid)

        # Find discrepancies
        discrepancies = []
        scanned_set = set(scanned_tags)
        expected_set = set(expected_tag_uids)

        # Missing items (expected but not scanned)
        for tag_uid in expected_set - scanned_set:
            discrepancies.append(
                InventoryDiscrepancy(
                    tag_uid=tag_uid,
                    expected_location=location,
                    actual_location=None,
                    status="missing",
                )
            )

        # Misplaced items (scanned but not expected at this location)
        for tag_uid in scanned_set - expected_set:
            tag = await self.tag_repo.get_by_tag_uid(tag_uid)
            if tag and tag.item_id:
                item = await self.item_repo.get(tag.item_id)
                expected_loc = item.location if item else None
                discrepancies.append(
                    InventoryDiscrepancy(
                        tag_uid=tag_uid,
                        expected_location=expected_loc,
                        actual_location=location,
                        status="misplaced",
                    )
                )

        return {
            "scan_id": scan_id,
            "location": location,
            "scanner_id": scanner_id,
            "timestamp": datetime.now(timezone.utc),
            "total_scanned": len(scanned_tags),
            "items_found": len(scanned_set & expected_set),
            "items_missing": len(expected_set - scanned_set),
            "items_misplaced": len(scanned_set - expected_set),
            "discrepancies": discrepancies,
        }

    async def get_inventory_report(
        self,
        scan_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Get detailed inventory report for a scan."""
        # In a real implementation, this would retrieve from a stored scan
        # For now, return a placeholder
        return {
            "scan_id": scan_id,
            "discrepancies": [],
            "timestamp": datetime.now(timezone.utc),
        }
