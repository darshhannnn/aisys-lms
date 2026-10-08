"""AC08: Dashboard generation and filterable statistics.

Acceptance test for dashboard and reporting (FR08).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.circulation import Loan, LoanStatus
from app.models.member import Member
from app.repositories.member import MemberRepository
from app.schemas.member import MemberCreate
from app.services.reporting import ReportingService


@pytest.mark.acceptance
class TestAC08Dashboard:
    """Acceptance tests for dashboards and reports (AC08)."""

    async def _make_member(self, db_session):
        member_repo = MemberRepository(Member, db_session)
        return await member_repo.create(
            MemberCreate(
                member_number=f"AC08-{uuid.uuid4().hex[:10]}",
                full_name="AC08 Member",
                email=f"ac08-{uuid.uuid4().hex[:6]}@example.edu",
            )
        )

    async def _seed_loan(self, db_session, member_id, item_id, *, due_offset: int, returned: bool):
        loan = Loan(
            member_id=member_id,
            item_id=item_id,
            due_date=date.today() + timedelta(days=due_offset),
            status=LoanStatus.RETURNED if returned else LoanStatus.ACTIVE,
            returned_at=datetime.now(timezone.utc) if returned else None,
        )
        db_session.add(loan)
        await db_session.flush()
        return loan

    async def _seed_item(self, db_session):
        from app.models.catalogue import BibliographicRecord, Item
        from app.schemas.catalogue import ItemCreate
        from app.repositories.catalogue import ItemRepository

        record = BibliographicRecord(
            title=f"AC08 Book {uuid.uuid4().hex[:8]}",
            author="AC08 Author",
            isbn=f"AC08-{uuid.uuid4().hex[:12]}",
        )
        db_session.add(record)
        await db_session.flush()
        return await ItemRepository(Item, db_session).create(
            ItemCreate(
                accession_number=f"AC08-ACC-{uuid.uuid4().hex[:8]}",
                barcode=f"AC08-BAR-{uuid.uuid4().hex[:8]}",
                bibliographic_record_id=record.id,
            )
        )

    @pytest.mark.asyncio
    async def test_dashboard_generation(self, client, db_session):
        """The dashboard endpoint returns live statistics with all keys."""
        member = await self._make_member(db_session)
        item = await self._seed_item(db_session)
        await self._seed_loan(db_session, member.id, item.id, due_offset=14, returned=False)

        response = await client.get("/api/v1/reports/dashboard")
        assert response.status_code == 200
        stats = response.json()

        for key in (
            "total_records",
            "total_items",
            "checked_out",
            "available",
            "total_members",
            "unpaid_fines_total",
        ):
            assert key in stats, f"dashboard missing {key}"
        assert stats["checked_out"] >= 1
        assert stats["total_members"] >= 1

    @pytest.mark.asyncio
    async def test_filterable_statistics(self, db_session):
        """ReportingService statistics reflect seeded circulation state."""
        service = ReportingService(db_session)
        member = await self._make_member(db_session)
        item1 = await self._seed_item(db_session)
        item2 = await self._seed_item(db_session)
        await self._seed_loan(db_session, member.id, item1.id, due_offset=14, returned=False)
        await self._seed_loan(db_session, member.id, item2.id, due_offset=-3, returned=False)

        stats = await service.get_dashboard_stats()
        assert stats["total_records"] >= 1
        assert stats["total_items"] >= 2
        assert stats["active_loans"] >= 2
        assert stats["overdue_loans"] >= 1  # item2 is past due

    @pytest.mark.asyncio
    async def test_circulation_report(self, db_session):
        """The circulation report counts checkouts within a date window."""
        service = ReportingService(db_session)
        member = await self._make_member(db_session)
        item = await self._seed_item(db_session)
        loan = await self._seed_loan(
            db_session, member.id, item.id, due_offset=14, returned=False
        )
        loan.issued_at = datetime.now(timezone.utc)
        db_session.add(loan)
        await db_session.flush()

        report = await service.get_circulation_report(
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=1),
        )
        assert report["new_checkouts"] >= 1

    @pytest.mark.asyncio
    async def test_member_activity_report(self, db_session):
        """The member activity report includes the member's loans."""
        service = ReportingService(db_session)
        member = await self._make_member(db_session)
        item = await self._seed_item(db_session)
        await self._seed_loan(db_session, member.id, item.id, due_offset=14, returned=False)

        report = await service.get_member_activity_report(member.id)
        assert report["member_id"] == member.id
        assert report["active_loans"] >= 1
        assert report["outstanding_fines"] >= 0.0
