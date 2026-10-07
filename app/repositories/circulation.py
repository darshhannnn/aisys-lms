"""Circulation repository.

Data access layer for Loan, Renewal, and Fine models.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional, Sequence

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.circulation import Loan, Renewal, Fine
from app.repositories.base import BaseRepository
from app.schemas.circulation import LoanCreate, LoanUpdate, FineCreate, FineUpdate


class LoanRepository(BaseRepository[Loan, LoanCreate, LoanUpdate]):
    """Repository for Loan model."""

    async def get_active_loans_by_member(
        self,
        member_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Loan]:
        """Get active loans for a member."""
        result = await self.session.execute(
            select(Loan)
            .where(Loan.member_id == member_id)
            .where(Loan.returned_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_loans_by_item(self, item_id: uuid.UUID) -> Optional[Loan]:
        """Get active loan for an item."""
        result = await self.session.execute(
            select(Loan)
            .where(Loan.item_id == item_id)
            .where(Loan.returned_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_overdue_loans(
        self,
        as_of_date: date,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Loan]:
        """Get overdue loans as of a specific date."""
        result = await self.session.execute(
            select(Loan)
            .where(Loan.due_date < as_of_date)
            .where(Loan.returned_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_active_loans_by_member(self, member_id: uuid.UUID) -> int:
        """Count active loans for a member."""
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count())
            .select_from(Loan)
            .where(Loan.member_id == member_id)
            .where(Loan.returned_at.is_(None))
        )
        return result.scalar()

    async def get_loans_due_soon(
        self,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Loan]:
        """Get loans due within a date range."""
        result = await self.session.execute(
            select(Loan)
            .where(Loan.due_date >= start_date)
            .where(Loan.due_date <= end_date)
            .where(Loan.returned_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class RenewalRepository:
    """Repository for Renewal model (simple class without generic base)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_loan_id(self, loan_id: uuid.UUID) -> Sequence[Renewal]:
        """Get all renewals for a loan."""
        result = await self.session.execute(
            select(Renewal)
            .where(Renewal.loan_id == loan_id)
            .order_by(Renewal.renewed_at)
        )
        return result.scalars().all()

    async def count_by_loan_id(self, loan_id: uuid.UUID) -> int:
        """Count renewals for a loan."""
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count())
            .select_from(Renewal)
            .where(Renewal.loan_id == loan_id)
        )
        return result.scalar()

    async def create(self, **kwargs) -> Renewal:
        """Create a new renewal."""
        db_obj = Renewal(**kwargs)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj


class FineRepository(BaseRepository[Fine, FineCreate, FineUpdate]):
    """Repository for Fine model."""

    async def get_by_member_id(
        self,
        member_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Fine]:
        """Get fines for a member."""
        result = await self.session.execute(
            select(Fine)
            .where(Fine.member_id == member_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_unpaid_fines_by_member(
        self,
        member_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Fine]:
        """Get unpaid fines for a member."""
        result = await self.session.execute(
            select(Fine)
            .where(Fine.member_id == member_id)
            .where(Fine.status != "paid")
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_loan_id(self, loan_id: uuid.UUID) -> Sequence[Fine]:
        """Get fines for a loan."""
        result = await self.session.execute(
            select(Fine)
            .where(Fine.loan_id == loan_id)
        )
        return result.scalars().all()

    async def sum_unpaid_fines_by_member(self, member_id: uuid.UUID) -> float:
        """Sum unpaid fines for a member."""
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.sum(Fine.amount - Fine.paid_amount))
            .select_from(Fine)
            .where(Fine.member_id == member_id)
            .where(Fine.status != "paid")
        )
        return result.scalar() or 0.0
