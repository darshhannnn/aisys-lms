"""AC02: Locate bibliographic item and associate RFID tag.

Acceptance test for catalogue and RFID tagging (FR01, FR03, FR05).
"""
from __future__ import annotations

import uuid

import pytest

from app.services.catalogue import CatalogueService
from app.services.tagging import TaggingService


@pytest.mark.acceptance
class TestAC02CatalogueRFID:
    """Acceptance tests for catalogue and RFID operations (AC02)."""

    @pytest.mark.asyncio
    async def test_locate_bibliographic_item(self, db_session):
        """A bibliographic record can be created and located by ISBN/search."""
        catalogue = CatalogueService(db_session)

        record = await catalogue.create_bibliographic_record(
            title="Distributed Systems",
            author="Andrew Tanenbaum",
            isbn="AC02-ISBN-0001",
        )
        assert record.id is not None

        # Locate by ISBN
        found = await catalogue.record_repo.get_by_isbn("AC02-ISBN-0001")
        assert found is not None
        assert found.title == "Distributed Systems"

    @pytest.mark.asyncio
    async def test_rfid_tag_association(self, db_session):
        """An RFID tag can be associated with a physical item (FR05)."""
        catalogue = CatalogueService(db_session)
        tagging = TaggingService(db_session)

        record = await catalogue.create_bibliographic_record(
            title="RFID Handbook", author="Klaus Finkenzeller", isbn="AC02-ISBN-0002"
        )
        item = await catalogue.create_item(
            barcode=f"AC02-BAR-{uuid.uuid4().hex[:8]}",
            bibliographic_record_id=record.id,
        )

        tag_uid = f"TAG-AC02-{uuid.uuid4().hex[:10].upper()}"
        tag, linked_item = await tagging.associate_tag_with_item(tag_uid, item.id)

        assert tag.tag_uid == tag_uid
        assert tag.item_id == item.id
        assert linked_item.id == item.id

        # Reverse lookup both ways
        found_item = await tagging.get_item_by_tag(tag_uid)
        assert found_item is not None and found_item.id == item.id
        found_tag = await tagging.get_tag_by_item(item.id)
        assert found_tag is not None and found_tag.tag_uid == tag_uid

    @pytest.mark.asyncio
    async def test_validation_logic(self, db_session):
        """Validation: unknown items and duplicate ISBNs are rejected."""
        catalogue = CatalogueService(db_session)
        tagging = TaggingService(db_session)

        # Tagging against a nonexistent item must fail
        with pytest.raises(ValueError, match="Item not found"):
            await tagging.associate_tag_with_item(
                f"TAG-AC02-INVALID-{uuid.uuid4().hex[:6]}", uuid.uuid4()
            )

        # Duplicate ISBN must be detected rather than silently duplicated
        await catalogue.create_bibliographic_record(
            title="First Edition", author="A. Author", isbn="AC02-ISBN-DUP"
        )
        existing = await catalogue.record_repo.get_by_isbn("AC02-ISBN-DUP")
        assert existing is not None

        # Duplicate ISBN must be rejected outright
        with pytest.raises(ValueError, match="already exists"):
            await catalogue.create_bibliographic_record(
                title="Second Edition", author="B. Author", isbn="AC02-ISBN-DUP"
            )

    @pytest.mark.asyncio
    async def test_tag_dissociation(self, db_session):
        """A tag can be dissociated from its item cleanly."""
        catalogue = CatalogueService(db_session)
        tagging = TaggingService(db_session)

        record = await catalogue.create_bibliographic_record(
            title="Temporary Title", author="Temp Author", isbn="AC02-ISBN-0003"
        )
        item = await catalogue.create_item(
            barcode=f"AC02-BAR-{uuid.uuid4().hex[:8]}",
            bibliographic_record_id=record.id,
        )
        tag_uid = f"TAG-AC02-{uuid.uuid4().hex[:10].upper()}"
        await tagging.associate_tag_with_item(tag_uid, item.id)

        updated_tag = await tagging.dissociate_tag_from_item(tag_uid)
        assert updated_tag.item_id is None
        assert await tagging.get_item_by_tag(tag_uid) is None
