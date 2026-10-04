"""Mock staff reader adapter.

Simulates a staff desk RFID reader for check-out/check-in operations.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.rfid.adapters.base import BaseRfidAdapter, ReadResult, TagReadEvent, WriteResult


@dataclass
class MockStaffReaderAdapter(BaseRfidAdapter):
    """Mock staff desk RFID reader.

    Simulates reading tags placed on a staff circulation desk.
    Used for check-out and check-in operations (AC03).
    """

    adapter_id: str = "mock_staff_reader"
    reader_id: str = "STAFF_DESK_01"
    mock_delay_s: float = 0.5  # Simulate hardware latency

    async def read_tag(self, timeout_s: float = 10.0) -> TagReadEvent:
        """Simulate reading a tag from the staff desk."""
        await asyncio.sleep(self.mock_delay_s)

        # In a real implementation, this would wait for actual hardware
        # For mock, we return a simulated event
        return TagReadEvent(
            tag_uid=f"MOCK_TAG_{datetime.now(timezone.utc).timestamp()}",
            reader_id=self.reader_id,
            result=ReadResult.SUCCESS,
            security_bit=False,
        )

    async def write_tag(self, tag_uid: str, data: dict) -> WriteResult:
        """Simulate writing data to a tag (e.g., setting security bit)."""
        await asyncio.sleep(self.mock_delay_s)

        # Simulate successful write
        return WriteResult(
            success=True,
            tag_uid=tag_uid,
        )

    async def is_online(self) -> bool:
        """Mock reader is always online."""
        return True

    async def read_multiple_tags(
        self,
        count: int = 1,
        timeout_s: float = 10.0,
    ) -> list[TagReadEvent]:
        """Simulate reading multiple tags in batch."""
        events = []
        for i in range(count):
            event = await self.read_tag(timeout_s / count)
            events.append(event)
        return events
