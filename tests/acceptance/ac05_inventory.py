"""AC05: Handheld reader mock for shelf inventory.

Acceptance test for inventory operations (FR06).
"""
from __future__ import annotations

import uuid

import pytest

from app.models.catalogue import BibliographicRecord, Item
from app.repositories.catalogue import ItemRepository
from app.repositories.rfid import RfidTagRepository
from app.schemas.catalogue import ItemCreate
from app.services.inventory import InventoryService
from app.models.rfid import RfidTag


@pytest.mark.acceptance
class TestAC05Inventory:
    """Acceptance tests for handheld shelf inventory (AC05)."""

    async def _seed_shelf(self, db_session, shelf: str, tag_uids: list[str]):
        """Create items at ``shelf`` with the given tags attached."""
        record = BibliographicRecord(
            title=f"AC05 Book {shelf}", author="AC05 Author", isbn=f"AC05-{uuid.uuid4().hex[:12]}"
        )
        db_session.add(record)
        await db_session.flush()

        item_repo = ItemRepository(Item, db_session)
        tag_repo = RfidTagRepository(RfidTag, db_session)

        items = []
        for uid in tag_uids:
            item = await item_repo.create(
                ItemCreate(
                    accession_number=f"AC05-ACC-{uid[-8:]}",
                    barcode=f"AC05-BAR-{uid[-8:]}",
                    bibliographic_record_id=record.id,
                    location=shelf,
                )
            )
            tag = RfidTag(tag_uid=uid, item_id=item.id, tag_type="item")
            db_session.add(tag)
            await db_session.flush()
            items.append((item, tag))
        return items

    @pytest.mark.asyncio
    async def test_handheld_inventory_scan(self, db_session):
        """A full scan of a shelf reports every item present (FR06)."""
        service = InventoryService(db_session)
        tag_uids = [f"TAG-AC05-A-{i:03d}-{uuid.uuid4().hex[:6]}" for i in range(3)]
        shelf = "SHELF-AC05-A"
        await self._seed_shelf(db_session, shelf, tag_uids)

        result = await service.scan_inventory(
            location=shelf, scanned_tags=tag_uids, scanner_id="HANDHELD-AC05"
        )

        assert result["total_scanned"] == 3
        assert result["items_found"] == 3
        assert result["items_missing"] == 0
        assert result["items_misplaced"] == 0

    @pytest.mark.asyncio
    async def test_missing_item_detection(self, db_session):
        """An expected tag absent from the scan is reported missing (AC05)."""
        service = InventoryService(db_session)
        tag_uids = [f"TAG-AC05-B-{i:03d}-{uuid.uuid4().hex[:6]}" for i in range(3)]
        shelf = "SHELF-AC05-B"
        await self._seed_shelf(db_session, shelf, tag_uids)

        # Scan with one tag missing from the handheld read
        scanned = tag_uids[:2]
        result = await service.scan_inventory(location=shelf, scanned_tags=scanned)

        assert result["items_found"] == 2
        assert result["items_missing"] == 1
        missing = [d for d in result["discrepancies"] if d.status == "missing"]
        assert len(missing) == 1
        assert missing[0].tag_uid == tag_uids[2]

    @pytest.mark.asyncio
    async def test_misplaced_item_detection(self, db_session):
        """A tag that belongs on another shelf is reported misplaced (AC05)."""
        service = InventoryService(db_session)
        home_tags = [f"TAG-AC05-C-{i:03d}-{uuid.uuid4().hex[:6]}" for i in range(2)]
        away_tags = [f"TAG-AC05-D-{i:03d}-{uuid.uuid4().hex[:6]}" for i in range(1)]
        await self._seed_shelf(db_session, "SHELF-AC05-C", home_tags)
        await self._seed_shelf(db_session, "SHELF-AC05-D", away_tags)

        # Scan shelf C with a tag from shelf D included
        scanned = home_tags + away_tags
        result = await service.scan_inventory(location="SHELF-AC05-C", scanned_tags=scanned)

        assert result["items_missing"] == 0
        assert result["items_misplaced"] == 1
        misplaced = [d for d in result["discrepancies"] if d.status == "misplaced"]
        assert len(misplaced) == 1
        assert misplaced[0].tag_uid == away_tags[0]
        assert misplaced[0].expected_location == "SHELF-AC05-D"
        assert misplaced[0].actual_location == "SHELF-AC05-C"

    @pytest.mark.asyncio
    async def test_inventory_report_generation(self, db_session):
        """The scan result carries a full report: counts, id and discrepancies."""
        service = InventoryService(db_session)
        tag_uids = [f"TAG-AC05-E-{i:03d}-{uuid.uuid4().hex[:6]}" for i in range(4)]
        shelf = "SHELF-AC05-E"
        await self._seed_shelf(db_session, shelf, tag_uids)

        result = await service.scan_inventory(location=shelf, scanned_tags=tag_uids[1:])

        # Report structure (generated from the scan, not stored state)
        assert result["scan_id"] is not None
        assert result["location"] == shelf
        assert result["scanner_id"] is None
        assert result["timestamp"] is not None
        assert result["total_scanned"] == 3
        assert result["items_found"] == 3
        assert result["items_missing"] == 1
        assert len(result["discrepancies"]) == 1
