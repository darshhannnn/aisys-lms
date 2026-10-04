"""Members API — CRUD and blocking (FR04, AC04)."""
from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.member import Member, MemberStatus

log = structlog.get_logger(__name__)
router = APIRouter()


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    member_number: str
    full_name: str
    category: str
    status: str
    outstanding_fine: float
    notify_email: bool
    notify_sms: bool


class MemberCreate(BaseModel):
    member_number: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    category: str = "student"
    patron_card_barcode: str | None = None


class BlockRequest(BaseModel):
    reason: str


@router.post("", response_model=MemberOut, status_code=201, summary="Create member")
async def create_member(body: MemberCreate, db: AsyncSession = Depends(get_db)) -> MemberOut:
    member = Member(**body.model_dump())
    db.add(member)
    await db.flush()
    log.info("member_created", member_number=member.member_number)
    return MemberOut.model_validate(member)


@router.get("/{member_id}", response_model=MemberOut, summary="Get member")
async def get_member(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> MemberOut:
    member = await db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return MemberOut.model_validate(member)


@router.post("/{member_id}/block", response_model=MemberOut, summary="Block a member (AC04)")
async def block_member(
    member_id: uuid.UUID,
    body: BlockRequest,
    db: AsyncSession = Depends(get_db),
) -> MemberOut:
    """Block a member from borrowing (AC04, FR04)."""
    member = await db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.status = MemberStatus.BLOCKED
    member.block_reason = body.reason
    log.warning("member_blocked", member_number=member.member_number, reason=body.reason)
    return MemberOut.model_validate(member)


@router.post("/{member_id}/unblock", response_model=MemberOut, summary="Unblock a member")
async def unblock_member(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> MemberOut:
    member = await db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.status = MemberStatus.ACTIVE
    member.block_reason = None
    log.info("member_unblocked", member_number=member.member_number)
    return MemberOut.model_validate(member)
