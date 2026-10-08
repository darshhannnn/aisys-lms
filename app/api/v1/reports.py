"""Reports and dashboard API (FR08, AC08)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.catalogue import BibliographicRecord, Item
from app.models.circulation import Fine, FineStatus, Loan, LoanStatus
from app.models.member import Member
from app.models.rfid import GateEvent, RfidTag

router = APIRouter()


@router.get("/dashboard", summary="Dashboard statistics (AC08, FR08)")
async def dashboard(db: AsyncSession = Depends(get_db)) -> dict:
    """Return live library-usage statistics for the dashboard."""
    total_records = (await db.execute(select(func.count()).select_from(BibliographicRecord))).scalar() or 0
    total_items = (await db.execute(select(func.count()).select_from(Item))).scalar() or 0
    checked_out = (await db.execute(select(func.count()).select_from(Loan).where(Loan.status == LoanStatus.ACTIVE))).scalar() or 0
    total_members = (await db.execute(select(func.count()).select_from(Member))).scalar() or 0
    tagged_items = (await db.execute(select(func.count()).select_from(RfidTag))).scalar() or 0
    unpaid_fines_result = await db.execute(select(func.sum(Fine.amount)).where(Fine.status == FineStatus.UNPAID))
    unpaid_fines = float(unpaid_fines_result.scalar() or 0)
    gate_events_today = (await db.execute(select(func.count()).select_from(GateEvent))).scalar() or 0

    return {
        "total_records": total_records,
        "total_items": total_items,
        "checked_out": checked_out,
        "available": total_items - checked_out,
        "total_members": total_members,
        "tagged_items": tagged_items,
        "unpaid_fines_total": unpaid_fines,
        "gate_events_today": gate_events_today,
    }
