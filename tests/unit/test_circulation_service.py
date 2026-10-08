"""Unit tests for circulation service."""
from __future__ import annotations

import pytest
from datetime import date, timedelta
from app.services.circulation import CirculationService
from app.models.circulation import Loan
from app.models.member import Member, MemberStatus
from app.models.catalogue import BibliographicRecord, Item


@pytest.mark.unit
class TestCirculationService:
    """Unit tests for CirculationService."""

    @pytest.mark.asyncio
    async def test_check_circulation_eligibility_success(self, db_session):
        """Test checking circulation eligibility for eligible member."""
        service = CirculationService(db_session)
        # Create test member
        from app.repositories.member import MemberRepository
        member_repo = MemberRepository(Member, db_session)
        from app.schemas.member import MemberCreate
        member = await member_repo.create(MemberCreate(
            member_number="MEM001",
            full_name="Test Member",
            email="test@example.com",
        ))
        can_borrow, reason = await service.check_circulation_eligibility(member.id)
        assert can_borrow is True
        assert reason is None

    @pytest.mark.asyncio
    async def test_check_circulation_eligibility_blocked(self, db_session):
        """Test checking circulation eligibility for blocked member."""
        service = CirculationService(db_session)
        # Create blocked member
        from app.repositories.member import MemberRepository
        member_repo = MemberRepository(Member, db_session)
        from app.schemas.member import MemberCreate
        member = await member_repo.create(MemberCreate(
            member_number="MEM002",
            full_name="Blocked Member",
            status=MemberStatus.BLOCKED,
            block_reason="Fine limit exceeded",
        ))
        can_borrow, reason = await service.check_circulation_eligibility(member.id)
        assert can_borrow is False
        assert reason is not None

    @pytest.mark.asyncio
    async def test_checkout_item(self, db_session):
        """Test checking out an item."""
        service = CirculationService(db_session)
        # Create test member and item
        from app.repositories.member import MemberRepository
        from app.repositories.catalogue import BibliographicRecordRepository, ItemRepository
        from app.schemas.member import MemberCreate
        from app.schemas.catalogue import BibliographicRecordCreate, ItemCreate

        member_repo = MemberRepository(Member, db_session)
        record_repo = BibliographicRecordRepository(BibliographicRecord, db_session)
        item_repo = ItemRepository(Item, db_session)

        member = await member_repo.create(MemberCreate(
            member_number="MEM003",
            full_name="Test Member",
        ))
        record = await record_repo.create(BibliographicRecordCreate(
            title="Test Book",
            author="Test Author",
        ))
        item = await item_repo.create(ItemCreate(
            accession_number="ACC-TEST-001",
            barcode="ITEM001",
            bibliographic_record_id=record.id,
        ))

        loan = await service.checkout_item(
            member_id=member.id,
            item_id=item.id,
            due_date=date.today() + timedelta(days=14),
        )
        assert loan.member_id == member.id
        assert loan.item_id == item.id
