"""SIP2 adapter client boundary.

Implements the SIP2 protocol for RFID-to-ILMS communication.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.rfid.adapters.base import BaseRfidAdapter, ReadResult, TagReadEvent, WriteResult


@dataclass
class SIP2Adapter(BaseRfidAdapter):
    """SIP2 protocol adapter.

    Provides boundary for SIP2 communication with external ILMS systems.
    In the mock prototype, this simulates SIP2 responses.
    """

    adapter_id: str = "sip2"
    host: str = "localhost"
    port: int = 6001
    institution_id: str = "AISYS"

    async def read_tag(self, timeout_s: float = 10.0) -> TagReadEvent:
        """Read tag via SIP2 protocol."""
        await asyncio.sleep(0.2)

        return TagReadEvent(
            tag_uid=f"SIP2_TAG_{datetime.now(timezone.utc).timestamp()}",
            reader_id="SIP2_GATEWAY",
            result=ReadResult.SUCCESS,
        )

    async def write_tag(self, tag_uid: str, data: dict) -> WriteResult:
        """Write tag via SIP2 protocol."""
        await asyncio.sleep(0.2)

        return WriteResult(
            success=True,
            tag_uid=tag_uid,
        )

    async def is_online(self) -> bool:
        """Check if SIP2 server is reachable."""
        # In production, this would connect to the SIP2 port
        return True

    async def checkout(
        self,
        item_barcode: str,
        patron_barcode: str,
    ) -> dict:
        """Perform SIP2 checkout request."""
        await asyncio.sleep(0.3)

        return {
            "success": True,
            "due_date": "2024-12-31",
            "item_barcode": item_barcode,
            "patron_barcode": patron_barcode,
        }

    async def checkin(
        self,
        item_barcode: str,
    ) -> dict:
        """Perform SIP2 checkin request."""
        await asyncio.sleep(0.3)

        return {
            "success": True,
            "item_barcode": item_barcode,
            "checkin_date": datetime.now(timezone.utc).isoformat(),
        }

    async def status(self) -> dict:
        """Get SIP2 server status."""
        await asyncio.sleep(0.1)

        return {
            "status": "ok",
            "message": "SIP2 server online",
        }
