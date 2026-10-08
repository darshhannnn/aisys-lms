"""Circulation service.

Business logic for loans, renewals, fines, and circulation rules (FR04, AC03, AC04).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.circulation import Loan, Fine
from app.models.member import Member, MemberStatus
from app.models.catalogue import Item, ItemStatus
from app.repositories.circulation import LoanRepository, RenewalRepository, FineRepository
from app.repositories.member import MemberRepository
from app.repositories.catalogue import ItemRepository


class CirculationService:
    """Circulation business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.loan_repo = LoanRepository(Loan, session)
        self.renewal_repo = RenewalRepository(session)
        self.fine_repo = FineRepository(Fine, session)
        self.member_repo = MemberRepository(Member, session)
        self.item_repo = ItemRepository(Item, session)

    async def check_circulation_eligibility(
        self,
        member_id: uuid.UUID,
    ) -> tuple[bool, str | None]:
        """Check if member can borrow items (FR04, AC04).

        Returns:
            (can_borrow, block_reason)
        """
        member = await self.member_repo.get(member_id)
        if not member:
            return False, "Member not found"

        if member.status == MemberStatus.BLOCKED:
            return False, member.block_reason or "Member is blocked"

        if member.status != MemberStatus.ACTIVE:
            return False, f"Member status is {member.status.value}"

        # Check fine limit
        if member.outstanding_fine > settings.max_fine_before_block:
            return False, f"Outstanding fine exceeds limit: ${member.outstanding_fine:.2f}"

        # Check loan limit
        active_loans = await self.loan_repo.count_active_loans_by_member(member_id)
        max_loans = 10  # Configurable per category
        if active_loans >= max_loans:
            return False, f"Maximum loan limit reached ({max_loans})"

        return True, None

    async def checkout_item(
        self,
        member_id: uuid.UUID,
        item_id: uuid.UUID,
        due_date: date,
    ) -> Loan:
        """Check out an item to a member (AC03)."""
        # Check eligibility
        can_borrow, block_reason = await self.check_circulation_eligibility(member_id)
        if not can_borrow:
            raise ValueError(block_reason or "Cannot borrow")

        # Check if item is available
        item = await self.item_repo.get(item_id)
        if not item:
            raise ValueError("Item not found")
        if item.status != "available":
            raise ValueError(f"Item is not available (status: {item.status})")
        if item.is_reference:
            raise ValueError("Reference items cannot be checked out")

        # Check if item already has active loan
        active_loan = await self.loan_repo.get_active_loans_by_item(item_id)
        if active_loan:
            raise ValueError("Item already checked out")

        # Create loan
        from app.schemas.circulation import LoanCreate

        loan_data = LoanCreate(
            member_id=member_id,
            item_id=item_id,
            due_date=due_date,
        )
        loan = await self.loan_repo.create(loan_data)

        # Update item status
        await self.item_repo.update(item, {"status": ItemStatus.CHECKED_OUT})

        return loan

    async def return_item(
        self,
        item_id: uuid.UUID,
        return_date: date | None = None,
    ) -> Loan:
        """Return an item (AC03)."""
        loan = await self.loan_repo.get_active_loans_by_item(item_id)
        if not loan:
            raise ValueError("No active loan found for this item")

        if return_date is None:
            return_date = date.today()

        # Check for overdue and create fine if needed
        if return_date > loan.due_date:
            days_overdue = (return_date - loan.due_date).days
            fine_amount = days_overdue * settings.fine_per_day
            await self.create_fine(
                member_id=loan.member_id,
                loan_id=loan.id,
                amount=fine_amount,
                reason=f"Overdue: {days_overdue} days",
                fine_type="overdue",
            )

        # Update loan
        from app.models.circulation import LoanStatus
        from app.schemas.circulation import LoanUpdate

        return_datetime = datetime.combine(return_date, datetime.min.time())
        updated_loan = await self.loan_repo.update(
            loan,
            LoanUpdate(returned_at=return_datetime, status=LoanStatus.RETURNED.value),
        )

        # Update item status
        item = await self.item_repo.get(item_id)
        await self.item_repo.update(item, {"status": ItemStatus.AVAILABLE})

        return updated_loan

    async def renew_loan(
        self,
        loan_id: uuid.UUID,
        new_due_date: date,
        renewed_by_id: uuid.UUID,
        notes: str | None = None,
    ) -> tuple[Loan, object]:
        """Renew a loan (AC03)."""
        loan = await self.loan_repo.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        if loan.returned_at is not None:
            raise ValueError("Cannot renew returned loan")

        # Check renewal limit
        renewal_count = await self.renewal_repo.count_by_loan_id(loan_id)
        if renewal_count >= settings.max_renewals:
            raise ValueError("Maximum renewal limit reached")

        # Create renewal record
        previous_due_date = loan.due_date
        renewal = await self.renewal_repo.create(
            loan_id=loan_id,
            previous_due_date=previous_due_date,
            new_due_date=new_due_date,
            renewed_by_id=renewed_by_id,
            notes=notes,
        )

        # Update loan
        from app.schemas.circulation import LoanUpdate

        updated_loan = await self.loan_repo.update(
            loan,
            LoanUpdate(due_date=new_due_date),
        )

        return updated_loan, renewal

    async def create_fine(
        self,
        member_id: uuid.UUID,
        loan_id: uuid.UUID,
        amount: float,
        reason: str,
        fine_type: str = "overdue",
    ) -> Fine:
        """Create a fine."""
        from app.schemas.circulation import FineCreate

        fine_data = FineCreate(
            member_id=member_id,
            loan_id=loan_id,
            amount=amount,
            reason=reason,
            fine_type=fine_type,
        )
        fine = await self.fine_repo.create(fine_data)

        # Update member's outstanding fine
        member = await self.member_repo.get(member_id)
        if member:
            member.outstanding_fine += amount
            self.session.add(member)
            await self.session.flush()

        return fine

    async def pay_fine(
        self,
        fine_id: uuid.UUID,
        paid_amount: float,
        payment_method: str = "cash",
        notes: str | None = None,
    ) -> Fine:
        """Pay a fine."""
        fine = await self.fine_repo.get(fine_id)
        if not fine:
            raise ValueError("Fine not found")

        from app.schemas.circulation import FineUpdate

        updated_fine = await self.fine_repo.update(
            fine,
            FineUpdate(
                status="paid" if (fine.paid_amount + paid_amount) >= fine.amount else "partial",
                paid_amount=fine.paid_amount + paid_amount,
                paid_date=date.today(),
                notes=notes,
            ),
        )

        # Update member's outstanding fine
        member = await self.member_repo.get(fine.member_id)
        if member:
            member.outstanding_fine -= paid_amount
            if member.outstanding_fine < 0:
                member.outstanding_fine = 0
            self.session.add(member)
            await self.session.flush()

        return updated_fine

    async def block_member(
        self,
        member_id: uuid.UUID,
        block_reason: str,
        blocked_by_id: uuid.UUID,
    ) -> Member:
        """Block a member from borrowing (FR04, AC04)."""
        member = await self.member_repo.get(member_id)
        if not member:
            raise ValueError("Member not found")

        member.status = MemberStatus.BLOCKED
        member.block_reason = block_reason
        member.blocked_by_id = blocked_by_id
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)

        return member

    async def unblock_member(
        self,
        member_id: uuid.UUID,
        unblocked_by_id: uuid.UUID | None = None,
    ) -> Member:
        """Lift a circulation block (FR04, AC04)."""
        member = await self.member_repo.get(member_id)
        if not member:
            raise ValueError("Member not found")

        member.status = MemberStatus.ACTIVE
        member.block_reason = None
        if unblocked_by_id is not None:
            member.blocked_by_id = unblocked_by_id
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)

        return member
