"""Gate events service.

Business logic for security gate events and alerts (FR07, AC06).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rfid import GateEvent
from app.models.member import Member
from app.models.catalogue import Item
from app.models.notification import Notification, NotificationType, NotificationChannel
from app.repositories.rfid import GateEventRepository
from app.repositories.member import MemberRepository
from app.repositories.catalogue import ItemRepository
from app.rfid.adapters.mock_gate import MockGateAdapter


class GateEventsService:
    """Gate events business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.gate_repo = GateEventRepository(session)
        self.member_repo = MemberRepository(Member, session)
        self.item_repo = ItemRepository(Item, session)
        self.gate_adapter = MockGateAdapter()

    async def process_gate_event(
        self,
        gate_id: str,
        tag_uids: list[str],
        event_type: str = "exit",
    ) -> GateEvent:
        """Process a gate event and detect unauthorized removals (FR07, AC06)."""
        # Get mock gate event data
        gate_data = await self.gate_adapter.read_tags(gate_id)
        is_alert = False
        alert_reason = None
        member_id = None

        # Check each tag
        for tag_uid in tag_uids:
            # Look up item by tag
            from app.services.tagging import TaggingService

            tagging_service = TaggingService(self.session)
            item = await tagging_service.get_item_by_tag(tag_uid)

            if item:
                # Check if item is checked out
                from app.repositories.circulation import LoanRepository
                from app.models.circulation import Loan

                loan_repo = LoanRepository(Loan, self.session)
                active_loan = await loan_repo.get_active_loans_by_item(item.id)

                if not active_loan and event_type == "exit":
                    # Item leaving without checkout - ALERT
                    is_alert = True
                    alert_reason = f"Unauthorized removal: item {item.barcode} not checked out"
                    break

                # If there's an active loan, get the member
                if active_loan:
                    member_id = active_loan.member_id

        # Create gate event
        event = await self.gate_repo.create(
            gate_id=gate_id,
            event_type=event_type,
            tag_uid=tag_uids[0] if tag_uids else None,
            accession_number=tag_uids[0] if tag_uids else None,  # Use tag_uid as accession for now
            cctv_image_path=gate_data.get("cctv_image_url") if is_alert else None,
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

        # Create notification record - use accession number to find member if possible
        if event.accession_number:
            # Try to find associated member through loans
            from app.repositories.catalogue import ItemRepository
            from app.models.catalogue import Item
            item_repo = ItemRepository(Item, self.session)
            # This is a simplified version - in production, would need proper lookup
            notification = Notification(
                member_id=uuid.uuid4(),  # Placeholder - would need actual member lookup
                channel=NotificationChannel.EMAIL,
                status="pending",
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
