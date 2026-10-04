"""Mock handheld reader adapter.

Simulates a handheld RFID reader for inventory operations.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.rfid.adapters.base import BaseRfidAdapter, ReadResult, TagReadEvent, WriteResult


@dataclass
class MockHandheldAdapter(BaseRfidAdapter):
    """Mock handheld RFID reader.

    Simulates a portable handheld reader used for shelf inventory (FR06, AC05).
    """

    adapter_id: str = "mock_handheld"
    reader_id: str = "HANDHELD_01"
    mock_delay_s: float = 0.3  # Faster than staff reader

    async def read_tag(self, timeout_s: float = 10.0) -> TagReadEvent:
        """Simulate reading a tag with the handheld scanner."""
        await asyncio.sleep(self.mock_delay_s)

        return TagReadEvent(
            tag_uid=f"MOCK_HANDHELD_TAG_{datetime.now(timezone.utc).timestamp()}",
            reader_id=self.reader_id,
            result=ReadResult.SUCCESS,
            security_bit=False,
        )

    async def write_tag(self, tag_uid: str, data: dict) -> WriteResult:
        """Simulate writing to a tag (handheld typically read-only)."""
        await asyncio.sleep(self.mock_delay_s)

        # Handheld readers are typically read-only
        return WriteResult(
            success=False,
            tag_uid=tag_uid,
            error="Handheld reader is read-only",
        )

    async def is_online(self) -> bool:
        """Mock handheld is always online."""
        return True

    async def continuous_scan(
        self,
        duration_s: float = 30.0,
        callback: Optional[callable] = None,
    ) -> list[TagReadEvent]:
        """Simulate continuous scanning for inventory."""
        events = []
        start_time = datetime.now(timezone.utc)

        while (datetime.now(timezone.utc) - start_time).total_seconds() < duration_s:
            event = await self.read_tag(timeout_s=1.0)
            events.append(event)

            if callback:
                await callback(event)

            await asyncio.sleep(0.5)  # Simulate scan interval

        return events
