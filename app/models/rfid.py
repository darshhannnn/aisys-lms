"""RFID ORM models: RfidTag, GateEvent, InventoryScan.

Implements:
- FR05: tag–item association, tag monitoring
- FR06: inventory / shelf management
- FR07: security gate events, CCTV photo, email notification
- AC02, AC05, AC06
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.catalogue import Item


class TagStatus(str, enum.Enum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    LOST = "lost"
    DAMAGED = "damaged"


class GateEventType(str, enum.Enum):
    AUTHORISED_EXIT = "authorised_exit"
    UNAUTHORISED_EXIT = "unauthorised_exit"   # AC06
    UNISSUED_ITEM = "unissued_item"
    ALARM_TRIGGERED = "alarm_triggered"
    FOOTFALL_ENTRY = "footfall_entry"
    FOOTFALL_EXIT = "footfall_exit"


class InventoryResult(str, enum.Enum):
    PRESENT = "present"
    MISSING = "missing"       # AC05
    MISPLACED = "misplaced"   # AC05 — on wrong shelf
    EXTRA = "extra"           # unexpected item found


class RfidTag(Base):
    """An RFID tag associated with an Item or Member.

    FR05: Each tag is validated before being linked to a bibliographic/item record.
    """

    __tablename__ = "rfid_tags"

    tag_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"), nullable=True, index=True
    )

    tag_type: Mapped[str] = mapped_column(String(16), default="item", nullable=False)  # "item" | "member"
    status: Mapped[TagStatus] = mapped_column(
        Enum(TagStatus, name="tag_status"), nullable=False, default=TagStatus.ACTIVE
    )

    # Security bit (FR07: can be read while LMS is offline)
    security_bit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Reader that last saw this tag
    last_seen_reader: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Tag was written by (for audit)
    tagged_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    item: Mapped[Item | None] = relationship("Item", back_populates="rfid_tag")

    def __repr__(self) -> str:
        return f"<RfidTag uid={self.tag_uid!r} status={self.status.value}>"


class GateEvent(Base):
    """Security gate alarm / footfall event (FR07, AC06).

    Records every gate alarm with accession number + optional CCTV image path.
    An email notification is queued immediately after unauthorised-removal events.
    """

    __tablename__ = "gate_events"

    event_type: Mapped[GateEventType] = mapped_column(
        Enum(GateEventType, name="gate_event_type"), nullable=False
    )
    gate_id: Mapped[str] = mapped_column(String(64), nullable=False)         # physical gate identifier
    tag_uid: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    accession_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Alert state (AC06 — unauthorised removal)
    is_alert: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    alert_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # CCTV photo (AC06) — stored path, not binary (offline storage)
    cctv_image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Email notification queued (AC06)
    notification_queued: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)  # original gate JSON

    def __repr__(self) -> str:
        return f"<GateEvent {self.event_type.value} gate={self.gate_id!r}>"


class InventoryScan(Base):
    """A single item read during a handheld inventory session (FR06, AC05).

    Groups of InventoryScans belong to an InventorySession.
    """

    __tablename__ = "inventory_scans"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_uid: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    accession_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expected_shelf: Mapped[str | None] = mapped_column(String(128), nullable=True)
    scanned_shelf: Mapped[str | None] = mapped_column(String(128), nullable=True)
    result: Mapped[InventoryResult] = mapped_column(
        Enum(InventoryResult, name="inventory_result"), nullable=False, default=InventoryResult.PRESENT
    )
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[InventorySession] = relationship("InventorySession", back_populates="scans")


class InventorySession(Base):
    """A complete handheld inventory run for a shelf range (AC05)."""

    __tablename__ = "inventory_sessions"

    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    shelf_range: Mapped[str] = mapped_column(String(255), nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_expected: Mapped[int | None] = mapped_column(nullable=True)
    total_scanned: Mapped[int | None] = mapped_column(nullable=True)

    scans: Mapped[list[InventoryScan]] = relationship(
        "InventoryScan", back_populates="session", lazy="select"
    )
