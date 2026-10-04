"""Abstract RFID adapter interface.

Every RFID device type (staff reader, handheld, gate, smart-card) implements
this base contract. When real hardware is unavailable, the mock implementation
is injected instead — without changing any business-logic code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ReadResult(str, Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    NO_TAG = "no_tag"
    ERROR = "error"
    DUPLICATE = "duplicate"


@dataclass
class TagReadEvent:
    """A single RFID tag-read event emitted by any reader type."""

    tag_uid: str
    reader_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    result: ReadResult = ReadResult.SUCCESS
    security_bit: bool | None = None
    raw_data: dict = field(default_factory=dict)


@dataclass
class WriteResult:
    success: bool
    tag_uid: str
    error: str | None = None


class BaseRfidAdapter(ABC):
    """Abstract base for all RFID adapters.

    Concrete implementations:
    - ``MockStaffReaderAdapter``   — staff desk reader (mock)
    - ``MockHandheldAdapter``      — handheld inventory reader (mock)
    - ``MockGateAdapter``          — security gate (mock)
    - ``MockSmartCardAdapter``     — smart-card credential provider (mock)

    Each implementation must handle:
    - Retries  (settings.rfid_retry_attempts)
    - Timeouts (settings.rfid_event_timeout_seconds)
    - Duplicate-event deduplication
    - Offline behaviour (queue events locally when LMS unreachable)
    """

    adapter_id: str = "base"

    @abstractmethod
    async def read_tag(self, timeout_s: float = 10.0) -> TagReadEvent:
        """Block until a tag is read or timeout is reached."""
        ...

    @abstractmethod
    async def write_tag(self, tag_uid: str, data: dict) -> WriteResult:
        """Write data (e.g. security bit) to a tag."""
        ...

    @abstractmethod
    async def is_online(self) -> bool:
        """Return True if the physical device is reachable."""
        ...

    async def health_check(self) -> dict:
        """Return a health-check dict for the /health endpoint."""
        online = await self.is_online()
        return {
            "adapter": self.adapter_id,
            "online": online,
            "status": "ok" if online else "degraded",
        }
