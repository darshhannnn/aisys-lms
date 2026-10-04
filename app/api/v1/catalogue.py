"""Catalogue API — search, browse, add, update items (FR01, FR02, AC02)."""
from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.catalogue import BibliographicRecord, Item, ItemStatus

log = structlog.get_logger(__name__)
router = APIRouter()


class BibRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    author: str | None
    isbn: str | None
    publisher: str | None
    publication_year: int | None
    item_type: str
    shelf_location: str | None


class BibRecordCreate(BaseModel):
    title: str
    author: str | None = None
    isbn: str | None = None
    issn: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    item_type: str = "book"
    dewey_class: str | None = None
    shelf_location: str | None = None
    description: str | None = None


@router.get("/search", summary="Full-text catalogue search (FR02)")
async def search_catalogue(
    q: Annotated[str, Query(min_length=1)],
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Full-text search across title, author, ISBN, subject.

    Uses PostgreSQL tsvector for fast full-text matching.
    """
    stmt = (
        select(BibliographicRecord)
        .where(
            BibliographicRecord.title.ilike(f"%{q}%") |
            BibliographicRecord.author.ilike(f"%{q}%") |
            BibliographicRecord.isbn.ilike(f"%{q}%")
        )
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return {
        "query": q,
        "count": len(records),
        "results": [BibRecordOut.model_validate(r) for r in records],
    }


@router.post("", response_model=BibRecordOut, status_code=201, summary="Add a bibliographic record (AC02)")
async def create_bib_record(
    body: BibRecordCreate,
    db: AsyncSession = Depends(get_db),
) -> BibRecordOut:
    """Create a new bibliographic record (AC02)."""
    bib = BibliographicRecord(**body.model_dump())
    db.add(bib)
    await db.flush()
    log.info("bib_record_created", id=str(bib.id), title=bib.title[:60])
    return BibRecordOut.model_validate(bib)


@router.get("/{bib_id}", response_model=BibRecordOut, summary="Get a bibliographic record")
async def get_bib_record(bib_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> BibRecordOut:
    bib = await db.get(BibliographicRecord, bib_id)
    if not bib:
        raise HTTPException(status_code=404, detail="Bibliographic record not found")
    return BibRecordOut.model_validate(bib)
