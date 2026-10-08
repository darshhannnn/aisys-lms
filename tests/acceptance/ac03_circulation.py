"""AC03: Check-out/in/renew via flow, auditable transaction history.

Acceptance test for circulation operations (FR04).
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.models.catalogue import ItemStatus
from app.repositories.catalogue import ItemRepository
from app.services.catalogue import CatalogueService
from app.services.circulation import CirculationService


@pytest.mark.acceptance
class TestAC03Circulation:
    """Acceptance tests for the circulation flow (AC03)."""

    async def _make_member(self, service: CirculationService, suffix: str):
        from app.repositories.member import MemberRepository
        from app.schemas.member import MemberCreate
        from app.models.member import Member

        member_repo = MemberRepository(Member, service.session)
        return await member_repo.create(
            MemberCreate(
                member_number=f"AC03-{suffix}-{uuid.uuid4().hex[:8]}",
                full_name="AC03 Test Member",
                email=f"ac03-{suffix}-{uuid.uuid4().hex[:6]}@example.edu",
            )
        )

    async def _make_available_item(self, service: CirculationService, suffix: str):
        catalogue = CatalogueService(service.session)
        record = await catalogue.create_bibliographic_record(
            title=f"AC03 Book {suffix}",
            author="AC03 Author",
            isbn=f"AC03-{suffix}-{uuid.uuid4().hex[:8]}",
        )
        return await catalogue.create_item(
            barcode=f"AC03-BAR-{suffix}-{uuid.uuid4().hex[:8]}",
            bibliographic_record_id=record.id,
        )

    @pytest.mark.asyncio
    async def test_checkout_logic(self, db_session):
        """Check-out creates a loan and flips the item to checked_out."""
        service = CirculationService(db_session)
        member = await self._make_member(service, "co")
        item = await self._make_available_item(service, "co")

        loan = await service.checkout_item(
            member_id=member.id,
            item_id=item.id,
            due_date=date.today() + timedelta(days=14),
        )

        assert loan.member_id == member.id
        assert loan.item_id == item.id
        assert loan.returned_at is None

        item_repo = ItemRepository(type(item), db_session)
        refreshed = await item_repo.get(item.id)
        assert refreshed.status == ItemStatus.CHECKED_OUT

    @pytest.mark.asyncio
    async def test_checkin_logic(self, db_session):
        """Check-in marks the loan returned and re-opens the item."""
        service = CirculationService(db_session)
        member = await self._make_member(service, "ci")
        item = await self._make_available_item(service, "ci")

        await service.checkout_item(
            member_id=member.id,
            item_id=item.id,
            due_date=date.today() + timedelta(days=14),
        )
        returned = await service.return_item(item_id=item.id)

        assert returned.returned_at is not None
        item_repo = ItemRepository(type(item), db_session)
        refreshed = await item_repo.get(item.id)
        assert refreshed.status == ItemStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_renewal_logic(self, db_session):
        """Renewal extends the due date and records a renewal entry."""
        service = CirculationService(db_session)
        member = await self._make_member(service, "rn")
        item = await self._make_available_item(service, "rn")

        loan = await service.checkout_item(
            member_id=member.id,
            item_id=item.id,
            due_date=date.today() + timedelta(days=14),
        )
        original_due = loan.due_date

        new_due = date.today() + timedelta(days=28)
        renewed, renewal = await service.renew_loan(
            loan_id=loan.id,
            new_due_date=new_due,
            renewed_by_id=uuid.uuid4(),
        )

        assert renewed.due_date == new_due
        assert renewal.previous_due_date == original_due
        count = await service.renewal_repo.count_by_loan_id(loan.id)
        assert count == 1

    @pytest.mark.asyncio
    async def test_audit_trail_verification(self, db_session):
        """The full loan lifecycle stays queryable after return (auditable)."""
        service = CirculationService(db_session)
        member = await self._make_member(service, "au")
        item = await self._make_available_item(service, "au")

        loan = await service.checkout_item(
            member_id=member.id,
            item_id=item.id,
            due_date=date.today() + timedelta(days=14),
        )
        await service.return_item(item_id=item.id)

        # Loan history must persist after check-in
        loan_repo = service.loan_repo
        history = await loan_repo.get_active_loans_by_item(item.id)
        assert history is None  # no longer active...

        from app.repositories.circulation import LoanRepository
        from app.models.circulation import Loan

        archived = await LoanRepository(Loan, db_session).get(loan.id)
        assert archived is not None
        assert archived.member_id == member.id
        assert archived.item_id == item.id
        assert archived.issued_at is not None
        assert archived.returned_at is not None
