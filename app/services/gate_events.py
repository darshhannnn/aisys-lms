"""Gate events service.

Business logic for security gate events and alerts (FR07, AC06).
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalogue import Item
from app.models.member import Member
from app.models.notification import Notification, NotificationChannel, NotificationType
from app.models.rfid import GateEvent, GateEventType
from app.repositories.catalogue import ItemRepository
from app.repositories.member import MemberRepository
from app.repositories.rfid import GateEventRepository
from app.integrations.cctv.mock import MockCCTVProvider
from app.rfid.adapters.mock_gate import MockGateAdapter

# Physical movement strings used by gate hardware → internal enum values
_MOVEMENT_MAP: dict[str, GateEventType] = {
    "entry": GateEventType.FOOTFALL_ENTRY,
    "exit": GateEventType.AUTHORISED_EXIT,
}


def resolve_event_type(raw: str, is_alert: bool) -> GateEventType:
    """Map a raw gate event string to a GateEventType.

    An exit that raised an alert is always an unauthorised exit;
    plain "entry"/"exit" strings map to footfall/authorised movement.
    """
    if is_alert and raw in ("exit", "unauthorised_exit", "alarm"):
        return GateEventType.UNAUTHORISED_EXIT
    if raw in _MOVEMENT_MAP:
        return _MOVEMENT_MAP[raw]
    try:
        return GateEventType(raw)
    except ValueError:
        return GateEventType.ALARM_TRIGGERED


class GateEventsService:
    """Gate events business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.gate_repo = GateEventRepository(session)
        self.member_repo = MemberRepository(Member, session)
        self.item_repo = ItemRepository(Item, session)
        self.gate_adapter = MockGateAdapter()
        self.cctv = MockCCTVProvider()

    async def process_gate_event(
        self,
        gate_id: str,
        tag_uids: list[str],
        event_type: str = "exit",
    ) -> GateEvent:
        """Process a gate event and detect unauthorized removals (FR07, AC06)."""
        gate_online = await self.gate_adapter.is_online()
        is_alert = False
        alert_reason = None
        member_id = None
        cctv_image_path = None

        # Check each tag
        for tag_uid in tag_uids:
            from app.services.tagging import TaggingService

            tagging_service = TaggingService(self.session)
            item = await tagging_service.get_item_by_tag(tag_uid)

            if item:
                # Check if item is checked out
                from app.models.circulation import Loan
                from app.repositories.circulation import LoanRepository

                loan_repo = LoanRepository(Loan, self.session)
                active_loan = await loan_repo.get_active_loans_by_item(item.id)

                if not active_loan and event_type == "exit":
                    # Item leaving without checkout - ALERT
                    is_alert = True
                    alert_reason = f"Unauthorized removal: item {item.barcode} not checked out"
                    break

                if active_loan:
                    member_id = active_loan.member_id

        # Capture a CCTV frame whenever the alarm fires (AC06)
        if is_alert and gate_online:
            cctv_result = await self.cctv.capture_frame(camera_id=f"CAM-{gate_id}")
            if cctv_result.success and cctv_result.frame:
                cctv_image_path = cctv_result.frame.image_url

        # Create gate event
        event = await self.gate_repo.create(
            gate_id=gate_id,
            event_type=resolve_event_type(event_type, is_alert),
            tag_uid=tag_uids[0] if tag_uids else None,
            accession_number=tag_uids[0] if tag_uids else None,  # Use tag_uid as accession for now
            member_id=member_id,
            is_alert=is_alert,
            alert_reason=alert_reason,
            cctv_image_path=cctv_image_path,
            notification_queued=False,
            raw_payload=str({"gate_id": gate_id, "tag_uids": tag_uids, "event_type": event_type}),
        )

        # If alert, queue notification
        if is_alert:
            await self._queue_alert_notification(event)

        return event

    async def _queue_alert_notification(self, event: GateEvent) -> None:
        """Queue notification for gate alert (FR09, AC06)."""
        # Mark notification as queued
        await self.gate_repo.update(event, notification_queued=True)

        notification = Notification(
            member_id=None,  # Gate alerts are routed to staff, not a patron
            channel=NotificationChannel.EMAIL,
            notification_type=NotificationType.GATE_ALERT,
            subject="Unauthorized Item Removal Alert",
            body=f"Alert: Unauthorized removal at gate {event.gate_id}",
            related_gate_event_id=event.id,
        )
        self.session.add(notification)
        await self.session.flush()

    async def get_recent_alerts(
        self,
        limit: int = 50,
    ) -> list[GateEvent]:
        """Get recent gate alerts."""
        return list(await self.gate_repo.get_alerts(skip=0, limit=limit))

    async def get_gate_events_by_gate(
        self,
        gate_id: str,
        limit: int = 100,
    ) -> list[GateEvent]:
        """Get events for a specific gate."""
        return list(await self.gate_repo.get_by_gate_id(gate_id, skip=0, limit=limit))
