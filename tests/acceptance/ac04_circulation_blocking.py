"""AC04: Block circulation for reference items or fine/limit exceedances.

Acceptance test for circulation blocking (FR04).
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.models.catalogue import BibliographicRecord, Item
from app.models.member import Member
from app.repositories.catalogue import ItemRepository
from app.repositories.member import MemberRepository
from app.schemas.catalogue import ItemCreate
from app.schemas.member import MemberCreate
from app.services.circulation import CirculationService


@pytest.mark.acceptance
class TestAC04CirculationBlocking:
    """Acceptance tests for circulation blocking (AC04)."""

    async def _make_member(self, service: CirculationService, suffix: str, **overrides):
        member_repo = MemberRepository(Member, service.session)
        data = MemberCreate(
            member_number=f"AC04-{suffix}-{uuid.uuid4().hex[:8]}",
            full_name="AC04 Member",
            email=f"ac04-{suffix}-{uuid.uuid4().hex[:6]}@example.edu",
        )
        member = await member_repo.create(data)
        for field, value in overrides.items():
            setattr(member, field, value)
        service.session.add(member)
        await service.session.flush()
        return member

    async def _make_item(self, service: CirculationService, suffix: str, **item_kwargs):
        from sqlalchemy import select

        result = await service.session.execute(
            select(BibliographicRecord).limit(1)
        )
        record = result.scalar_one_or_none()
        if record is None:
            record = BibliographicRecord(
                title="AC04 Record", author="AC04 Author", isbn=f"AC04-{uuid.uuid4().hex[:12]}"
            )
            service.session.add(record)
            await service.session.flush()

        item_repo = ItemRepository(Item, service.session)
        defaults = dict(
            accession_number=f"AC04-ACC-{suffix}-{uuid.uuid4().hex[:8]}",
            barcode=f"AC04-BAR-{suffix}-{uuid.uuid4().hex[:8]}",
            bibliographic_record_id=record.id,
        )
        defaults.update(item_kwargs)
        return await item_repo.create(ItemCreate(**defaults))

    @pytest.mark.asyncio
    async def test_reference_item_blocking(self, db_session):
        """Reference-only items can never be checked out."""
        service = CirculationService(db_session)
        member = await self._make_member(service, "ref")
        item = await self._make_item(service, "ref", is_reference=True)

        with pytest.raises(ValueError, match="[Rr]eference"):
            await service.checkout_item(
                member_id=member.id,
                item_id=item.id,
                due_date=date.today() + timedelta(days=14),
            )

    @pytest.mark.asyncio
    async def test_fine_limit_blocking(self, db_session):
        """A member above the outstanding-fine threshold is blocked."""
        service = CirculationService(db_session)
        member = await self._make_member(
            service, "fine", outstanding_fine=51.00  # limit is 50.00
        )
        can_borrow, reason = await service.check_circulation_eligibility(member.id)
        assert can_borrow is False
        assert "fine" in reason.lower()

    @pytest.mark.asyncio
    async def test_loan_limit_blocking(self, db_session):
        """A member at the maximum number of active loans is blocked."""
        from app.models.circulation import Loan, LoanStatus

        service = CirculationService(db_session)
        member = await self._make_member(service, "limit")
        item = await self._make_item(service, "limit")

        # Simulate 10 active loans directly (fast, no checkout ceremony)
        for i in range(10):
            loan = Loan(
                member_id=member.id,
                item_id=item.id,
                due_date=date.today() + timedelta(days=14),
                status=LoanStatus.ACTIVE,
            )
            service.session.add(loan)
        await service.session.flush()

        can_borrow, reason = await service.check_circulation_eligibility(member.id)
        assert can_borrow is False
        assert "limit" in reason.lower()

    @pytest.mark.asyncio
    async def test_unblock_logic(self, db_session):
        """Blocking prevents borrowing; unblocking restores eligibility."""
        service = CirculationService(db_session)
        member = await self._make_member(service, "unblk")

        blocked = await service.block_member(
            member.id, block_reason="AC04 test block", blocked_by_id=uuid.uuid4()
        )
        can_borrow, reason = await service.check_circulation_eligibility(blocked.id)
        assert can_borrow is False
        assert reason is not None

        unblocked = await service.unblock_member(member.id)
        assert unblocked.status.value == "active"
        assert unblocked.block_reason is None
        can_borrow, reason = await service.check_circulation_eligibility(unblocked.id)
        assert can_borrow is True
        assert reason is None
