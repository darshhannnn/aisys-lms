"""Circulation API — check-out, check-in, renewal, due-date, fine management.

Implements FR04, AC03, AC04.
"""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.catalogue import Item, ItemStatus
from app.models.circulation import CirculationBlockReason, Fine, FineStatus, Loan, LoanStatus
from app.models.member import Member, MemberStatus

log = structlog.get_logger(__name__)
router = APIRouter()


# ── Request / response schemas ────────────────────────────────────────────────

class CheckOutRequest(BaseModel):
    member_id: uuid.UUID
    item_id: uuid.UUID
    loan_days: int | None = None       # override default
    protocol: str = "direct"          # "direct" | "ncip" | "sip2"


class CheckOutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    loan_id: uuid.UUID
    due_date: date
    protocol: str
    block_reason: str | None = None
    success: bool


class CheckInRequest(BaseModel):
    item_id: uuid.UUID
    protocol: str = "direct"


class CheckInResponse(BaseModel):
    success: bool
    item_id: uuid.UUID
    fine_levied: float | None = None


class RenewalRequest(BaseModel):
    loan_id: uuid.UUID


class RenewalResponse(BaseModel):
    success: bool
    new_due_date: date | None = None
    reason: str | None = None


# ── Helper: circulation eligibility check (AC04) ──────────────────────────────

async def _assert_can_borrow(
    member: Member,
    item: Item,
    db: AsyncSession,
) -> None:
    """Raise HTTP 422 with a block reason if borrowing is not allowed (AC04)."""
    if member.status == MemberStatus.BLOCKED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"block_reason": CirculationBlockReason.MEMBER_BLOCKED.value,
                    "message": f"Member {member.member_number} is blocked: {member.block_reason}"},
        )
    if item.is_reference or item.status == ItemStatus.REFERENCE_ONLY:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"block_reason": CirculationBlockReason.REFERENCE_ITEM.value,
                    "message": "Reference items cannot be checked out"},
        )
    if member.outstanding_fine >= settings.max_fine_before_block:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"block_reason": CirculationBlockReason.FINE_LIMIT_EXCEEDED.value,
                    "message": f"Outstanding fine {member.outstanding_fine} exceeds limit {settings.max_fine_before_block}"},
        )
    if item.status != ItemStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"block_reason": CirculationBlockReason.ITEM_NOT_AVAILABLE.value,
                    "message": f"Item status is {item.status.value}"},
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/checkout", response_model=CheckOutResponse, summary="Check out an item (AC03, AC04)")
async def checkout(body: CheckOutRequest, db: AsyncSession = Depends(get_db)) -> CheckOutResponse:
    """Issue an item to a member.

    - Validates AC04 blocking rules before issuing.
    - Records the full loan event for auditable history (AC03).
    """
    member = await db.get(Member, body.member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    item = await db.get(Item, body.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await _assert_can_borrow(member, item, db)

    loan_days = body.loan_days or settings.default_loan_days
    due = date.today() + timedelta(days=loan_days)

    loan = Loan(
        member_id=body.member_id,
        item_id=body.item_id,
        status=LoanStatus.ACTIVE,
        due_date=due,
        protocol=body.protocol,
    )
    item.status = ItemStatus.CHECKED_OUT
    db.add(loan)
    await db.flush()

    log.info("checkout_success", loan_id=str(loan.id), member=member.member_number, item=item.accession_number)
    return CheckOutResponse(loan_id=loan.id, due_date=due, protocol=body.protocol, success=True)


@router.post("/checkin", response_model=CheckInResponse, summary="Check in (return) an item (AC03)")
async def checkin(body: CheckInRequest, db: AsyncSession = Depends(get_db)) -> CheckInResponse:
    """Return an item and calculate any overdue fine."""
    item = await db.get(Item, body.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Find the active loan
    result = await db.execute(
        select(Loan).where(Loan.item_id == body.item_id, Loan.status == LoanStatus.ACTIVE)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="No active loan found for this item")

    now = datetime.now(UTC)
    loan.returned_at = now
    loan.status = LoanStatus.RETURNED
    item.status = ItemStatus.AVAILABLE

    # Calculate overdue fine
    fine_amount = 0.0
    overdue_days = (date.today() - loan.due_date).days
    if overdue_days > 0:
        fine_amount = overdue_days * settings.fine_per_day
        fine = Fine(
            member_id=loan.member_id,
            loan_id=loan.id,
            amount=fine_amount,
            reason=f"Overdue by {overdue_days} day(s)",
            status=FineStatus.UNPAID,
        )
        db.add(fine)
        # Update denormalised outstanding fine on member
        member = await db.get(Member, loan.member_id)
        if member:
            member.outstanding_fine = float(member.outstanding_fine) + fine_amount

    log.info("checkin_success", loan_id=str(loan.id), fine=fine_amount)
    return CheckInResponse(success=True, item_id=body.item_id, fine_levied=fine_amount or None)


@router.post("/renew", response_model=RenewalResponse, summary="Renew a loan (AC03)")
async def renew(body: RenewalRequest, db: AsyncSession = Depends(get_db)) -> RenewalResponse:
    """Extend a loan's due date by the default loan period."""
    loan = await db.get(Loan, body.loan_id)
    if not loan or loan.status != LoanStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Active loan not found")
    if loan.renewals_count >= settings.max_renewals:
        return RenewalResponse(success=False, reason=f"Maximum {settings.max_renewals} renewals reached")

    old_due = loan.due_date
    new_due = old_due + timedelta(days=settings.default_loan_days)
    loan.due_date = new_due
    loan.renewals_count += 1

    log.info("renewal_success", loan_id=str(loan.id), new_due=str(new_due))
    return RenewalResponse(success=True, new_due_date=new_due)


@router.get("/due-date/{loan_id}", summary="Due date enquiry (FR04)")
async def due_date_enquiry(loan_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    """Return due date and renewal count for a loan."""
    loan = await db.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return {
        "loan_id": str(loan.id),
        "due_date": loan.due_date.isoformat(),
        "status": loan.status.value,
        "renewals_used": loan.renewals_count,
        "renewals_remaining": max(0, settings.max_renewals - loan.renewals_count),
    }
