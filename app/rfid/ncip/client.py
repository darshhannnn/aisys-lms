"""NCIP 2.0 adapter client boundary.

Implements the NCIP 2.0 protocol for RFID-to-ILMS communication.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.rfid.adapters.base import BaseRfidAdapter, ReadResult, TagReadEvent, WriteResult


@dataclass
class NCIPAdapter(BaseRfidAdapter):
    """NCIP 2.0 protocol adapter.

    Provides boundary for NCIP 2.0 communication with external ILMS systems.
    In the mock prototype, this simulates NCIP responses.
    """

    adapter_id: str = "ncip"
    endpoint: str = "http://localhost:9000/ncip"
    agency_id: str = "AISYS_LIB"

    async def read_tag(self, timeout_s: float = 10.0) -> TagReadEvent:
        """Read tag via NCIP protocol."""
        # In production, this would make an NCIP request
        await asyncio.sleep(0.2)

        return TagReadEvent(
            tag_uid=f"NCIP_TAG_{datetime.now(timezone.utc).timestamp()}",
            reader_id="NCIP_GATEWAY",
            result=ReadResult.SUCCESS,
        )

    async def write_tag(self, tag_uid: str, data: dict) -> WriteResult:
        """Write tag via NCIP protocol."""
        await asyncio.sleep(0.2)

        return WriteResult(
            success=True,
            tag_uid=tag_uid,
        )

    async def is_online(self) -> bool:
        """Check if NCIP endpoint is reachable."""
        # In production, this would ping the endpoint
        return True

    async def check_out_item(
        self,
        item_barcode: str,
        user_barcode: str,
    ) -> dict:
        """Perform NCIP CheckOutItem request."""
        await asyncio.sleep(0.3)

        return {
            "success": True,
            "due_date": "2024-12-31",
            "item_barcode": item_barcode,
            "user_barcode": user_barcode,
        }

    async def check_in_item(
        self,
        item_barcode: str,
    ) -> dict:
        """Perform NCIP CheckInItem request."""
        await asyncio.sleep(0.3)

        return {
            "success": True,
            "item_barcode": item_barcode,
            "check_in_date": datetime.now(timezone.utc).isoformat(),
        }
