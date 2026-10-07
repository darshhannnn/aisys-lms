"""RFID schemas.

Request/response models for RFID tags, events, and operations.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── RFID Tag Schemas ────────────────────────────────────────────────────────────
class RfidTagBase(BaseModel):
    """Base RFID tag fields."""

    tag_uid: str = Field(..., min_length=1, max_length=128)
    tag_type: str = Field(default="item", max_length=50)
    status: str = Field(default="active", max_length=50)


class RfidTagCreate(RfidTagBase):
    """RFID tag creation request."""

    item_id: Optional[uuid.UUID] = None


class RfidTagUpdate(BaseModel):
    """RFID tag update request."""

    item_id: Optional[uuid.UUID] = None
    status: Optional[str] = Field(None, max_length=50)


class RfidTagResponse(RfidTagBase):
    """RFID tag response (read-only)."""

    id: uuid.UUID
    item_id: Optional[uuid.UUID] = None
    member_id: Optional[uuid.UUID] = None
    security_bit: bool = True
    last_seen_reader: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RfidTagAssociateRequest(BaseModel):
    """Request to associate RFID tag with item (FR05, AC02)."""

    tag_uid: str = Field(..., min_length=1, max_length=128)
    item_id: uuid.UUID


# ── Gate Event Schemas ─────────────────────────────────────────────────────────
class GateEventBase(BaseModel):
    """Base gate event fields."""

    event_type: str = Field(..., max_length=50)  # entry, exit, alert
    gate_id: str = Field(..., min_length=1, max_length=64)
    tag_uid: Optional[str] = None
    accession_number: Optional[str] = None


class GateEventCreate(GateEventBase):
    """Gate event creation request."""

    pass


class GateEventResponse(GateEventBase):
    """Gate event response (read-only)."""

    id: uuid.UUID
    accession_number: Optional[str] = None
    cctv_image_path: Optional[str] = None
    notification_queued: bool = False
    notification_sent_at: Optional[datetime] = None
    raw_payload: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Inventory Schemas ──────────────────────────────────────────────────────────
class InventoryScanRequest(BaseModel):
    """Inventory scan request (FR06, AC05)."""

    location: str = Field(..., min_length=1, max_length=100)
    scanned_tags: list[str] = Field(..., min_length=1)
    scanner_id: Optional[str] = Field(None, max_length=64)


class InventoryScanResponse(BaseModel):
    """Inventory scan response."""

    scan_id: uuid.UUID
    location: str
    total_scanned: int
    items_found: int
    items_missing: int
    items_misplaced: int
    timestamp: datetime

    class Config:
        from_attributes = True


class InventoryDiscrepancy(BaseModel):
    """Individual inventory discrepancy."""

    tag_uid: str
    expected_location: Optional[str] = None
    actual_location: Optional[str] = None
    status: str  # missing, misplaced, found


class InventoryReportResponse(BaseModel):
    """Full inventory report with discrepancies."""

    scan_id: uuid.UUID
    location: str
    discrepancies: list[InventoryDiscrepancy]
    timestamp: datetime

    class Config:
        from_attributes = True
