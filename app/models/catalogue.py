"""Bibliographic and item catalogue ORM models.

Implements:
- FR01: Acquisition, cataloguing, OPAC, barcode/spine-label
- FR02: Full-text search (PostgreSQL tsvector column)
- FR05: RFID tag association to bibliographic/item record
"""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.circulation import Loan
    from app.models.rfid import RfidTag


class ItemType(str, enum.Enum):
    BOOK = "book"
    JOURNAL = "journal"
    SERIAL = "serial"
    THESIS = "thesis"
    MAP = "map"
    AV = "av"          # Audio-Visual
    DIGITAL = "digital"
    OTHER = "other"


class ItemStatus(str, enum.Enum):
    AVAILABLE = "available"
    CHECKED_OUT = "checked_out"
    RESERVED = "reserved"
    LOST = "lost"
    DAMAGED = "damaged"
    IN_TRANSIT = "in_transit"
    REFERENCE_ONLY = "reference_only"   # FR04: reference-book restrictions
    WITHDRAWN = "withdrawn"


class AcquisitionStatus(str, enum.Enum):
    ORDERED = "ordered"
    RECEIVED = "received"
    CATALOGUED = "catalogued"
    PROCESSED = "processed"


class BibliographicRecord(Base):
    """Bibliographic (title-level) record — the MARC-lite catalogue entry.

    One bibliographic record can have many physical Items.
    """

    __tablename__ = "bibliographic_records"

    # Core bibliographic fields
    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(512), nullable=True)
    author: Mapped[str | None] = mapped_column(String(512), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    issn: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    edition: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dewey_class: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lcc_class: Mapped[str | None] = mapped_column(String(64), nullable=True)

    item_type: Mapped[ItemType] = mapped_column(
        Enum(ItemType, name="item_type"), nullable=False, default=ItemType.BOOK
    )

    # Full-text search string (FR02 - simplified for SQLite)
    search_vector: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source of record (migration or original)
    source_system: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # Virtual bookshelf (FR02)
    shelf_location: Mapped[str | None] = mapped_column(String(128), nullable=True)

    items: Mapped[list[Item]] = relationship("Item", back_populates="bib_record", lazy="select")

    __table_args__ = (
        Index("ix_bib_title", "title"),
        Index("ix_bib_author", "author"),
    )

    def __repr__(self) -> str:
        return f"<BibliographicRecord {self.isbn or self.title[:40]!r}>"


class Item(Base):
    """Physical item (copy) — one per barcode / RFID tag.

    Links a physical copy to a BibliographicRecord.
    """

    __tablename__ = "items"

    bib_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bibliographic_records.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    accession_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    barcode: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    spine_label: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus, name="item_status"), nullable=False, default=ItemStatus.AVAILABLE
    )
    is_reference: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    acquisition_status: Mapped[AcquisitionStatus] = mapped_column(
        Enum(AcquisitionStatus, name="acquisition_status"),
        nullable=False,
        default=AcquisitionStatus.CATALOGUED,
    )

    # Cost tracking
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    bib_record: Mapped[BibliographicRecord] = relationship("BibliographicRecord", back_populates="items")
    rfid_tag: Mapped[RfidTag | None] = relationship("RfidTag", back_populates="item", uselist=False)
    loans: Mapped[list[Loan]] = relationship("Loan", back_populates="item", lazy="select")

    def __repr__(self) -> str:
        return f"<Item accession={self.accession_number!r} status={self.status.value}>"
