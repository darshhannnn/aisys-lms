"""Unit tests for catalogue service."""
from __future__ import annotations

import pytest
from app.services.catalogue import CatalogueService
from app.models.catalogue import BibliographicRecord, Item


@pytest.mark.unit
class TestCatalogueService:
    """Unit tests for CatalogueService."""

    @pytest.mark.asyncio
    async def test_create_bibliographic_record(self, db_session):
        """Test creating a bibliographic record."""
        service = CatalogueService(db_session)
        record = await service.create_bibliographic_record(
            title="Test Book",
            author="Test Author",
            isbn="1234567890",
        )
        assert record.title == "Test Book"
        assert record.author == "Test Author"
        assert record.isbn == "1234567890"

    @pytest.mark.asyncio
    async def test_create_item(self, db_session):
        """Test creating an item."""
        service = CatalogueService(db_session)
        record = await service.create_bibliographic_record(
            title="Test Book",
            author="Test Author",
        )
        item = await service.create_item(
            barcode="ITEM001",
            bibliographic_record_id=record.id,
        )
        assert item.barcode == "ITEM001"
        assert item.bibliographic_record_id == record.id

    @pytest.mark.asyncio
    async def test_search_records(self, db_session):
        """Test searching bibliographic records."""
        service = CatalogueService(db_session)
        await service.create_bibliographic_record(
            title="Python Programming",
            author="John Doe",
        )
        await service.create_bibliographic_record(
            title="Java Basics",
            author="Jane Smith",
        )
        results = await service.search_records("Python")
        assert len(results) > 0
        assert "Python" in results[0].title
