"""Catalogue schemas.

Request/response models for bibliographic records and items.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


# ── Bibliographic Record Schemas ───────────────────────────────────────────────
class BibliographicRecordBase(BaseModel):
    """Base bibliographic record fields."""

    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, max_length=20)
    issn: Optional[str] = Field(None, max_length=20)
    publisher: Optional[str] = Field(None, max_length=255)
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    edition: Optional[str] = Field(None, max_length=64)
    language: Optional[str] = Field(default="en", max_length=8)
    subject: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    dewey_class: Optional[str] = Field(None, max_length=64)
    lcc_class: Optional[str] = Field(None, max_length=64)


class BibliographicRecordCreate(BibliographicRecordBase):
    """Bibliographic record creation request."""

    pass


class BibliographicRecordUpdate(BaseModel):
    """Bibliographic record update request."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, max_length=20)
    issn: Optional[str] = Field(None, max_length=20)
    publisher: Optional[str] = Field(None, max_length=255)
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    edition: Optional[str] = Field(None, max_length=64)
    language: Optional[str] = Field(None, max_length=8)
    subject: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    dewey_class: Optional[str] = Field(None, max_length=64)
    lcc_class: Optional[str] = Field(None, max_length=64)


class BibliographicRecordResponse(BibliographicRecordBase):
    """Bibliographic record response (read-only)."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    item_count: int = 0  # Derived field

    class Config:
        from_attributes = True


class BibliographicRecordSearch(BaseModel):
    """Search query for bibliographic records (FR02)."""

    query: str = Field(..., min_length=1, description="Full-text search query")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ── Item Schemas ───────────────────────────────────────────────────────────────
class ItemBase(BaseModel):
    """Base item fields."""

    accession_number: str = Field(..., min_length=1, max_length=64)
    barcode: Optional[str] = Field(None, max_length=64)
    spine_label: Optional[str] = Field(None, max_length=64)
    status: str = Field(default="available", max_length=50)
    is_reference: bool = False
    price: Optional[float] = Field(None, ge=0)
    currency: str = Field(default="INR", max_length=3)
    vendor: Optional[str] = Field(None, max_length=255)


class ItemCreate(ItemBase):
    """Item creation request."""

    bibliographic_record_id: uuid.UUID


class ItemUpdate(BaseModel):
    """Item update request."""

    barcode: Optional[str] = Field(None, max_length=64)
    spine_label: Optional[str] = Field(None, max_length=64)
    status: Optional[str] = Field(None, max_length=50)
    is_reference: Optional[bool] = None
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    vendor: Optional[str] = Field(None, max_length=255)


class ItemResponse(ItemBase):
    """Item response (read-only)."""

    id: uuid.UUID
    bibliographic_record_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemWithRecordResponse(ItemResponse):
    """Item response with embedded bibliographic record."""

    bibliographic_record: BibliographicRecordResponse

    class Config:
        from_attributes = True
