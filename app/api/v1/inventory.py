"""Inventory API endpoints.

RFID inventory management for shelf operations (FR06, AC05).
"""
from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DatabaseSession, require_circulation_staff
from app.db.session import get_db
from app.services.inventory import InventoryService
from app.schemas.rfid import InventoryScanRequest, InventoryScanResponse

log = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/scan", response_model=InventoryScanResponse, summary="Perform inventory scan (AC05)")
async def scan_inventory(
    request: InventoryScanRequest,
    db: DatabaseSession,
    current_user: Annotated[object, Depends(require_circulation_staff)],
) -> dict:
    """Perform an inventory scan at a location using handheld RFID reader (FR06, AC05)."""
    service = InventoryService(db)
    result = await service.scan_inventory(
        location=request.location,
        scanned_tags=request.scanned_tags,
        scanner_id=request.scanner_id,
    )

    log.info(
        "inventory_scan_completed",
        location=request.location,
        total_scanned=result["total_scanned"],
        items_missing=result["items_missing"],
        items_misplaced=result["items_misplaced"],
    )

    return result


@router.get("/report/{scan_id}", summary="Get inventory report")
async def get_inventory_report(
    scan_id: str,
    db: DatabaseSession,
    current_user: Annotated[object, Depends(require_circulation_staff)],
) -> dict:
    """Get detailed inventory report for a specific scan."""
    from uuid import UUID

    service = InventoryService(db)
    result = await service.get_inventory_report(UUID(scan_id))
    return result
