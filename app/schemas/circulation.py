"""Circulation schemas.

Request/response models for loans, renewals, and fines.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


# ── Loan Schemas ───────────────────────────────────────────────────────────────
class LoanBase(BaseModel):
    """Base loan fields."""

    member_id: uuid.UUID
    item_id: uuid.UUID
    due_date: date


class LoanCreate(LoanBase):
    """Loan creation request (check-out)."""

    pass


class LoanUpdate(BaseModel):
    """Loan update request."""

    returned_at: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=50)


class LoanResponse(LoanBase):
    """Loan response (read-only)."""

    id: uuid.UUID
    issued_at: datetime
    returned_at: Optional[datetime] = None
    status: str
    renewals_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoanWithDetailsResponse(LoanResponse):
    """Loan response with embedded member and item details."""

    member_full_name: str
    member_number: str
    item_barcode: str
    item_title: str
    item_call_number: Optional[str] = None

    class Config:
        from_attributes = True


# ── Renewal Schemas ─────────────────────────────────────────────────────────────
class RenewalCreate(BaseModel):
    """Renewal creation request."""

    new_due_date: date
    notes: Optional[str] = Field(None, max_length=500)


class RenewalResponse(BaseModel):
    """Renewal response."""

    id: uuid.UUID
    loan_id: uuid.UUID
    previous_due_date: date
    new_due_date: date
    renewed_by_id: uuid.UUID
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Fine Schemas ───────────────────────────────────────────────────────────────
class FineBase(BaseModel):
    """Base fine fields."""

    member_id: uuid.UUID
    loan_id: uuid.UUID
    amount: float = Field(..., ge=0)
    reason: str = Field(..., min_length=1, max_length=255)
    fine_type: str = Field(default="overdue", max_length=50)


class FineCreate(FineBase):
    """Fine creation request."""

    pass


class FineUpdate(BaseModel):
    """Fine update request."""

    status: Optional[str] = Field(None, max_length=50)
    paid_amount: Optional[float] = Field(None, ge=0)
    paid_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)


class FineResponse(FineBase):
    """Fine response (read-only)."""

    id: uuid.UUID
    status: str
    paid_amount: float = 0.0
    paid_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FinePaymentRequest(BaseModel):
    """Fine payment request."""

    paid_amount: float = Field(..., gt=0)
    payment_method: str = Field(default="cash", max_length=50)
    notes: Optional[str] = Field(None, max_length=500)


# ── Circulation Check Schemas ───────────────────────────────────────────────────
class CirculationCheckRequest(BaseModel):
    """Request to check if a member can borrow (FR04, AC04)."""

    member_id: uuid.UUID


class CirculationCheckResponse(BaseModel):
    """Response indicating whether member can borrow."""

    can_borrow: bool
    block_reason: Optional[str] = None
    outstanding_fine: float = 0.0
    active_loans: int = 0
    max_loans: int = 10
