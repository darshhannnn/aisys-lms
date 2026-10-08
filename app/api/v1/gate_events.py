"""Gate events API endpoints.

Security gate event management and alerts (FR07, AC06).
"""
from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DatabaseSession, require_circulation_staff
from app.db.session import get_db
from app.services.gate_events import GateEventsService
from app.schemas.rfid import GateEventResponse
from pydantic import BaseModel

log = structlog.get_logger(__name__)
router = APIRouter()


class GateEventCreateRequest(BaseModel):
    """Gate event creation request."""

    gate_id: str
    event_type: str
    tag_uids: list[str]
    member_id: str | None = None


@router.post("/", response_model=GateEventResponse, summary="Record gate event (AC06)")
async def create_gate_event(
    request: GateEventCreateRequest,
    db: DatabaseSession,
    current_user: Annotated[object, require_circulation_staff],
):
    """Record a gate event and detect unauthorized removals (FR07, AC06)."""
    from uuid import UUID

    service = GateEventsService(db)
    event = await service.process_gate_event(
        gate_id=request.gate_id,
        tag_uids=request.tag_uids,
        event_type=request.event_type,
    )

    if event.is_alert:
        log.warning(
            "gate_alert_triggered",
            gate_id=request.gate_id,
            alert_reason=event.alert_reason,
            tag_count=len(request.tag_uids),
        )

    return event


@router.get("/alerts", summary="Get recent gate alerts")
async def get_gate_alerts(
    db: DatabaseSession,
    current_user: Annotated[object, require_circulation_staff],
    limit: int = 50,
):
    """Get recent gate security alerts."""
    service = GateEventsService(db)
    alerts = await service.get_recent_alerts(limit=limit)
    return alerts


@router.get("/gate/{gate_id}", summary="Get events for a specific gate")
async def get_gate_events(
    gate_id: str,
    db: DatabaseSession,
    current_user: Annotated[object, require_circulation_staff],
    limit: int = 100,
):
    """Get events for a specific security gate."""
    service = GateEventsService(db)
    events = await service.get_gate_events_by_gate(gate_id, limit=limit)
    return events
