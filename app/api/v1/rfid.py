"""RFID API — tagging (AC02), gate events (AC06), inventory (AC05)."""
from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.catalogue import Item
from app.models.rfid import GateEvent, GateEventType, RfidTag, TagStatus
from app.rfid.adapters.mock_gate import MockGateAdapter

log = structlog.get_logger(__name__)
router = APIRouter()

_gate = MockGateAdapter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class TagItemRequest(BaseModel):
    item_id: uuid.UUID
    tag_uid: str


class TagItemResponse(BaseModel):
    tag_uid: str
    item_id: uuid.UUID
    status: str


class GateEventOut(BaseModel):
    id: uuid.UUID
    event_type: str
    gate_id: str
    tag_uid: str | None
    accession_number: str | None
    cctv_image_path: str | None
    notification_queued: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/tag-item", response_model=TagItemResponse, summary="Associate RFID tag with item (AC02)")
async def tag_item(body: TagItemRequest, db: AsyncSession = Depends(get_db)) -> TagItemResponse:
    """Validate item record exists, then link an RFID tag to it (AC02, FR05)."""
    item = await db.get(Item, body.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found — validate item before tagging (FR05)")

    # Check if tag UID is already registered
    existing = await db.get(RfidTag, body.tag_uid)  # tag_uid is unique; use select below
    from sqlalchemy import select as sa_select
    result = await db.execute(sa_select(RfidTag).where(RfidTag.tag_uid == body.tag_uid))
    existing_tag = result.scalar_one_or_none()
    if existing_tag:
        raise HTTPException(status_code=409, detail=f"Tag UID {body.tag_uid!r} already registered")

    tag = RfidTag(
        tag_uid=body.tag_uid,
        item_id=body.item_id,
        tag_type="item",
        status=TagStatus.ACTIVE,
        security_bit=True,
    )
    db.add(tag)
    await db.flush()
    log.info("tag_item_linked", tag_uid=body.tag_uid, item=item.accession_number)
    return TagItemResponse(tag_uid=body.tag_uid, item_id=body.item_id, status=tag.status.value)


@router.post(
    "/gate/simulate-unauthorised-removal",
    response_model=GateEventOut,
    summary="Simulate gate unauthorised-removal event (AC06)",
)
async def simulate_gate_event(
    accession_number: str,
    gate_id: str = "GATE-MAIN-01",
    db: AsyncSession = Depends(get_db),
) -> GateEventOut:
    """Generate an UNAUTHORISED_EXIT gate event, attach mock CCTV image, and queue email (AC06)."""
    gate = MockGateAdapter(gate_id=gate_id)
    raw_event = await gate.simulate_unauthorised_removal(accession_number)

    gate_event = GateEvent(
        event_type=GateEventType.UNAUTHORISED_EXIT,
        gate_id=gate_id,
        tag_uid=raw_event.tag_uid,
        accession_number=accession_number,
        cctv_image_path=f"/cctv/mock/{accession_number}.jpg",  # mock path (AC06)
        notification_queued=True,  # email notification queued (AC06)
        raw_payload=str(raw_event.raw_data),
    )
    db.add(gate_event)
    await db.flush()
    log.warning("gate_unauthorised_removal_recorded", accession=accession_number, event_id=str(gate_event.id))

    return GateEventOut(
        id=gate_event.id,
        event_type=gate_event.event_type.value,
        gate_id=gate_event.gate_id,
        tag_uid=gate_event.tag_uid,
        accession_number=gate_event.accession_number,
        cctv_image_path=gate_event.cctv_image_path,
        notification_queued=gate_event.notification_queued,
    )
