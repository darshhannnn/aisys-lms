"""Member schemas.

Request/response models for library members (patrons).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.member import MemberCategory, MemberStatus


# ── Member Schemas ─────────────────────────────────────────────────────────────
class MemberBase(BaseModel):
    """Base member fields."""

    member_number: str = Field(..., min_length=1, max_length=32)
    full_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=32)
    category: MemberCategory = MemberCategory.STUDENT
    status: MemberStatus = MemberStatus.ACTIVE
    membership_start: Optional[date] = None
    membership_end: Optional[date] = None
    notify_email: bool = True
    notify_sms: bool = False
    notify_print: bool = False


class MemberCreate(MemberBase):
    """Member creation request."""

    national_id: Optional[str] = Field(None, max_length=64)
    patron_card_barcode: Optional[str] = Field(None, max_length=64)
    photo_url: Optional[str] = Field(None, max_length=512)
    source_system: Optional[str] = Field(None, max_length=64)
    source_id: Optional[str] = Field(None, max_length=128)


class MemberUpdate(BaseModel):
    """Member update request."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=32)
    category: Optional[MemberCategory] = None
    status: Optional[MemberStatus] = None
    membership_start: Optional[date] = None
    membership_end: Optional[date] = None
    patron_card_barcode: Optional[str] = Field(None, max_length=64)
    photo_url: Optional[str] = Field(None, max_length=512)
    notify_email: Optional[bool] = None
    notify_sms: Optional[bool] = None
    notify_print: Optional[bool] = None


class MemberBlockRequest(BaseModel):
    """Member blocking request (FR04, AC04)."""

    block_reason: str = Field(..., min_length=1, max_length=500)


class MemberResponse(MemberBase):
    """Member response (read-only)."""

    id: uuid.UUID
    national_id: Optional[str] = None
    patron_card_barcode: Optional[str] = None
    photo_url: Optional[str] = None
    block_reason: Optional[str] = None
    blocked_by_id: Optional[uuid.UUID] = None
    outstanding_fine: float = 0.0
    source_system: Optional[str] = None
    source_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemberSearch(BaseModel):
    """Search query for members."""

    query: str = Field(..., min_length=1, description="Search by name, member number, or email")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
