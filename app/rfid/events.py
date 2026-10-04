"""RFID event bus and handlers.

Provides an event-driven architecture for processing RFID events
from various adapters (staff, handheld, gate, smart-card).
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional

from app.rfid.adapters.base import TagReadEvent


class EventType(str, Enum):
    """Types of RFID events."""

    TAG_READ = "tag_read"
    TAG_WRITE = "tag_write"
    GATE_ENTRY = "gate_entry"
    GATE_EXIT = "gate_exit"
    CHECKOUT = "checkout"
    CHECKIN = "checkin"
    INVENTORY_SCAN = "inventory_scan"


@dataclass
class RfidEvent:
    """RFID event passed through the event bus."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.TAG_READ
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_adapter: str = "unknown"
    data: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class RfidEventBus:
    """Event bus for RFID events.

    Allows multiple handlers to subscribe to RFID events.
    """

    def __init__(self):
        self._handlers: dict[EventType, list[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[RfidEvent], None],
    ) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable[[RfidEvent], None],
    ) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: RfidEvent) -> None:
        """Publish an event to the bus."""
        await self._queue.put(event)

    async def start(self) -> None:
        """Start the event bus processing loop."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._process_events())

    async def stop(self) -> None:
        """Stop the event bus processing loop."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing event: {e}")

    async def _dispatch_event(self, event: RfidEvent) -> None:
        """Dispatch event to registered handlers."""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                print(f"Handler error for {event.event_type}: {e}")


# Global event bus instance
_event_bus: Optional[RfidEventBus] = None


def get_event_bus() -> RfidEventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = RfidEventBus()
    return _event_bus
