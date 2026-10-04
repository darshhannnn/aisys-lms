"""Mock gate adapter — simulates a security gate for testing (AC06).

Generates realistic gate events without any physical hardware.
Supports: unauthorised-removal, footfall, alarm events.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

import structlog

from app.rfid.adapters.base import BaseRfidAdapter, ReadResult, TagReadEvent, WriteResult

log = structlog.get_logger(__name__)


class MockGateAdapter(BaseRfidAdapter):
    """Mock security gate that emits configurable events for AC06 testing.

    Usage::

        gate = MockGateAdapter(gate_id="GATE-MAIN-01")
        event = await gate.simulate_unauthorised_removal("ACC-001234")
    """

    adapter_id = "mock_gate"

    def __init__(self, gate_id: str = "GATE-MOCK-01") -> None:
        self.gate_id = gate_id
        self._event_queue: asyncio.Queue[TagReadEvent] = asyncio.Queue()
        self._online = True

    # ── BaseRfidAdapter interface ─────────────────────────────────────────────

    async def read_tag(self, timeout_s: float = 10.0) -> TagReadEvent:
        """Wait for the next queued gate event."""
        try:
            event = await asyncio.wait_for(self._event_queue.get(), timeout=timeout_s)
            log.info("gate_event_read", gate_id=self.gate_id, tag_uid=event.tag_uid)
            return event
        except asyncio.TimeoutError:
            return TagReadEvent(
                tag_uid="",
                reader_id=self.gate_id,
                result=ReadResult.TIMEOUT,
            )

    async def write_tag(self, tag_uid: str, data: dict) -> WriteResult:
        """Gate adapters are read-only — write is a no-op."""
        return WriteResult(success=False, tag_uid=tag_uid, error="Gate adapter is read-only")

    async def is_online(self) -> bool:
        return self._online

    # ── Mock simulation helpers ───────────────────────────────────────────────

    async def simulate_unauthorised_removal(
        self,
        accession_number: str,
        tag_uid: str | None = None,
    ) -> TagReadEvent:
        """Queue an UNAUTHORISED_EXIT gate event (AC06)."""
        uid = tag_uid or f"MOCK-TAG-{uuid.uuid4().hex[:8].upper()}"
        event = TagReadEvent(
            tag_uid=uid,
            reader_id=self.gate_id,
            timestamp=datetime.utcnow(),
            result=ReadResult.SUCCESS,
            security_bit=True,  # security bit still armed = not checked out
            raw_data={
                "event_type": "unauthorised_exit",
                "accession_number": accession_number,
                "alarm": True,
            },
        )
        await self._event_queue.put(event)
        log.warning(
            "mock_gate_unauthorised_removal",
            gate_id=self.gate_id,
            accession_number=accession_number,
            tag_uid=uid,
        )
        return event

    async def simulate_footfall(self, direction: str = "entry") -> TagReadEvent:
        """Queue a footfall counting event."""
        event = TagReadEvent(
            tag_uid="",
            reader_id=self.gate_id,
            result=ReadResult.SUCCESS,
            raw_data={"event_type": f"footfall_{direction}"},
        )
        await self._event_queue.put(event)
        return event

    def set_offline(self, offline: bool = True) -> None:
        """Simulate gate going offline (for NFR01 / AC09 tests)."""
        self._online = not offline
        log.info("mock_gate_offline_state", gate_id=self.gate_id, offline=offline)
