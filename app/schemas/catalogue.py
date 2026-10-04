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
    edition: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)
    subject: Optional[str] = Field(None, max_length=255)
    abstract: Optional[str] = None
    call_number: Optional[str] = Field(None, max_length=100)
    material_type: str = Field(default="book", max_length=50)


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
    edition: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)
    subject: Optional[str] = Field(None, max_length=255)
    abstract: Optional[str] = None
    call_number: Optional[str] = Field(None, max_length=100)
    material_type: Optional[str] = Field(None, max_length=50)


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

    barcode: str = Field(..., min_length=1, max_length=64)
    call_number: Optional[str] = Field(None, max_length=100)
    location: str = Field(default="stacks", max_length=100)
    status: str = Field(default="available", max_length=50)
    item_type: str = Field(default="circulating", max_length=50)
    condition: str = Field(default="good", max_length=50)


class ItemCreate(ItemBase):
    """Item creation request."""

    bibliographic_record_id: uuid.UUID


class ItemUpdate(BaseModel):
    """Item update request."""

    call_number: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    item_type: Optional[str] = Field(None, max_length=50)
    condition: Optional[str] = Field(None, max_length=50)


class ItemResponse(ItemBase):
    """Item response (read-only)."""

    id: uuid.UUID
    bibliographic_record_id: uuid.UUID
    rfid_tag_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemWithRecordResponse(ItemResponse):
    """Item response with embedded bibliographic record."""

    bibliographic_record: BibliographicRecordResponse

    class Config:
        from_attributes = True
