"""Reporting service.

Business logic for dashboard statistics and reports (FR08, AC08).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalogue import BibliographicRecord, Item
from app.models.member import Member
from app.models.circulation import Loan, Fine
from app.models.rfid import GateEvent


class ReportingService:
    """Reporting and dashboard business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Get dashboard statistics (FR08, AC08)."""
        # Total bibliographic records
        result = await self.session.execute(
            select(func.count()).select_from(BibliographicRecord)
        )
        total_records = result.scalar() or 0

        # Total items
        result = await self.session.execute(
            select(func.count()).select_from(Item)
        )
        total_items = result.scalar() or 0

        # Available items
        result = await self.session.execute(
            select(func.count()).select_from(Item).where(Item.status == "available")
        )
        available_items = result.scalar() or 0

        # Total members
        result = await self.session.execute(
            select(func.count()).select_from(Member)
        )
        total_members = result.scalar() or 0

        # Active members
        result = await self.session.execute(
            select(func.count()).select_from(Member).where(Member.status == "active")
        )
        active_members = result.scalar() or 0

        # Active loans
        result = await self.session.execute(
            select(func.count())
            .select_from(Loan)
            .where(Loan.return_date.is_(None))
        )
        active_loans = result.scalar() or 0

        # Overdue loans
        today = date.today()
        result = await self.session.execute(
            select(func.count())
            .select_from(Loan)
            .where(Loan.due_date < today)
            .where(Loan.return_date.is_(None))
        )
        overdue_loans = result.scalar() or 0

        # Outstanding fines
        result = await self.session.execute(
            select(func.sum(Fine.amount - Fine.paid_amount))
            .select_from(Fine)
            .where(Fine.status != "paid")
        )
        outstanding_fines = result.scalar() or 0.0

        # Gate alerts in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        result = await self.session.execute(
            select(func.count())
            .select_from(GateEvent)
            .where(GateEvent.timestamp >= yesterday)
            .where(GateEvent.is_alert == True)
        )
        recent_alerts = result.scalar() or 0

        return {
            "total_records": total_records,
            "total_items": total_items,
            "available_items": available_items,
            "total_members": total_members,
            "active_members": active_members,
            "active_loans": active_loans,
            "overdue_loans": overdue_loans,
            "outstanding_fines": float(outstanding_fines),
            "recent_alerts": recent_alerts,
            "generated_at": datetime.now(timezone.utc),
        }

    async def get_circulation_report(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Get circulation report for a date range."""
        # Convert to datetime for timestamp fields
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # New checkouts in range
        result = await self.session.execute(
            select(func.count())
            .select_from(Loan)
            .where(Loan.checkout_date >= start_date)
            .where(Loan.checkout_date <= end_date)
        )
        new_checkouts = result.scalar() or 0

        # Returns in range
        result = await self.session.execute(
            select(func.count())
            .select_from(Loan)
            .where(Loan.return_date >= start_date)
            .where(Loan.return_date <= end_date)
        )
        returns = result.scalar() or 0

        # Fines created in range
        result = await self.session.execute(
            select(func.count())
            .select_from(Fine)
            .where(Fine.created_at >= start_datetime)
            .where(Fine.created_at <= end_datetime)
        )
        fines_created = result.scalar() or 0

        # Fines paid in range
        result = await self.session.execute(
            select(func.sum(Fine.paid_amount))
            .select_from(Fine)
            .where(Fine.paid_date >= start_date)
            .where(Fine.paid_date <= end_date)
        )
        fines_paid = result.scalar() or 0.0

        return {
            "start_date": start_date,
            "end_date": end_date,
            "new_checkouts": new_checkouts,
            "returns": returns,
            "fines_created": fines_created,
            "fines_paid": float(fines_paid),
        }

    async def get_member_activity_report(
        self,
        member_id: str,
    ) -> dict[str, Any]:
        """Get activity report for a specific member."""
        # Active loans
        result = await self.session.execute(
            select(func.count())
            .select_from(Loan)
            .where(Loan.member_id == member_id)
            .where(Loan.return_date.is_(None))
        )
        active_loans = result.scalar() or 0

        # Total fines
        result = await self.session.execute(
            select(func.sum(Fine.amount))
            .select_from(Fine)
            .where(Fine.member_id == member_id)
        )
        total_fines = result.scalar() or 0.0

        # Paid fines
        result = await self.session.execute(
            select(func.sum(Fine.paid_amount))
            .select_from(Fine)
            .where(Fine.member_id == member_id)
        )
        paid_fines = result.scalar() or 0.0

        return {
            "member_id": member_id,
            "active_loans": active_loans,
            "total_fines": float(total_fines),
            "paid_fines": float(paid_fines),
            "outstanding_fines": float(total_fines - paid_fines),
        }
