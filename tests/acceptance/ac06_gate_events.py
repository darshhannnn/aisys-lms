"""AC06: Unauthorised removal event from gate, CCTV image, email.

Acceptance test for gate events and notifications (FR07, FR09).
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.models.catalogue import BibliographicRecord, Item
from app.models.rfid import GateEventType, RfidTag
from app.repositories.catalogue import ItemRepository
from app.schemas.catalogue import ItemCreate
from app.services.circulation import CirculationService
from app.services.gate_events import GateEventsService


@pytest.mark.acceptance
class TestAC06GateEvents:
    """Acceptance tests for security gate events (AC06)."""

    async def _seed_tagged_item(self, db_session, tag_uid: str):
        """Create an item with an RFID tag, un-checked-out by default."""
        record = BibliographicRecord(
            title=f"AC06 Book {tag_uid[-6:]}",
            author="AC06 Author",
            isbn=f"AC06-{uuid.uuid4().hex[:12]}",
        )
        db_session.add(record)
        await db_session.flush()

        item_repo = ItemRepository(Item, db_session)
        item = await item_repo.create(
            ItemCreate(
                accession_number=f"AC06-ACC-{tag_uid[-8:]}",
                barcode=f"AC06-BAR-{tag_uid[-8:]}",
                bibliographic_record_id=record.id,
            )
        )
        tag = RfidTag(tag_uid=tag_uid, item_id=item.id, tag_type="item")
        db_session.add(tag)
        await db_session.flush()
        return item, tag

    async def _make_member(self, service: GateEventsService):
        from app.repositories.member import MemberRepository
        from app.schemas.member import MemberCreate
        from app.models.member import Member

        member_repo = MemberRepository(Member, service.session)
        return await member_repo.create(
            MemberCreate(
                member_number=f"AC06-{uuid.uuid4().hex[:10]}",
                full_name="AC06 Member",
                email=f"ac06-{uuid.uuid4().hex[:6]}@example.edu",
            )
        )

    @pytest.mark.asyncio
    async def test_unauthorized_removal_detection(self, db_session):
        """An un-checked-out item crossing the gate raises an alert (FR07)."""
        service = GateEventsService(db_session)
        tag_uid = f"TAG-AC06-{uuid.uuid4().hex[:10].upper()}"
        await self._seed_tagged_item(db_session, tag_uid)

        event = await service.process_gate_event(
            gate_id="GATE-AC06-01", tag_uids=[tag_uid], event_type="exit"
        )

        assert event.is_alert is True
        assert event.event_type == GateEventType.UNAUTHORISED_EXIT
        assert event.alert_reason is not None
        assert "not checked out" in event.alert_reason

    @pytest.mark.asyncio
    async def test_cctv_image_capture(self, db_session):
        """An alert triggers a (mock) CCTV frame capture attached to the event."""
        service = GateEventsService(db_session)
        service.cctv.clear()
        tag_uid = f"TAG-AC06-{uuid.uuid4().hex[:10].upper()}"
        await self._seed_tagged_item(db_session, tag_uid)

        event = await service.process_gate_event(
            gate_id="GATE-AC06-02", tag_uids=[tag_uid], event_type="exit"
        )

        assert event.is_alert is True
        assert event.cctv_image_path is not None
        assert "CAM-GATE-AC06-02" in event.cctv_image_path
        # The mock provider stored the frame for evidence review
        assert len(service.cctv.get_captured_frames()) == 1

    @pytest.mark.asyncio
    async def test_email_notification_queuing(self, db_session):
        """An alert queues an email notification linked to the gate event."""
        from sqlalchemy import select

        from app.models.notification import Notification, NotificationChannel, NotificationType

        service = GateEventsService(db_session)
        tag_uid = f"TAG-AC06-{uuid.uuid4().hex[:10].upper()}"
        await self._seed_tagged_item(db_session, tag_uid)

        event = await service.process_gate_event(
            gate_id="GATE-AC06-03", tag_uids=[tag_uid], event_type="exit"
        )

        assert event.notification_queued is True

        result = await db_session.execute(
            select(Notification).where(Notification.related_gate_event_id == event.id)
        )
        notification = result.scalar_one_or_none()
        assert notification is not None
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.notification_type == NotificationType.GATE_ALERT
        assert "Unauthorized" in notification.subject

    @pytest.mark.asyncio
    async def test_gate_event_logging(self, db_session):
        """Every gate crossing is logged and queryable per gate (AC06)."""
        service = GateEventsService(db_session)
        tag_uid = f"TAG-AC06-{uuid.uuid4().hex[:10].upper()}"
        item, _ = await self._seed_tagged_item(db_session, tag_uid)

        # Authorised path: the item IS checked out, so no alert
        circulation = CirculationService(db_session)
        member = await self._make_member(service)
        await circulation.checkout_item(
            member_id=member.id,
            item_id=item.id,
            due_date=date.today() + timedelta(days=14),
        )
        event = await service.process_gate_event(
            gate_id="GATE-AC06-04", tag_uids=[tag_uid], event_type="exit"
        )

        assert event.is_alert is False
        assert event.event_type == GateEventType.AUTHORISED_EXIT

        # Logged and retrievable
        events = await service.get_gate_events_by_gate("GATE-AC06-04")
        assert len(events) == 1
        assert events[0].id == event.id
        assert events[0].member_id == member.id
        alerts = await service.get_recent_alerts()
        assert all(e.gate_id != "GATE-AC06-04" or not e.is_alert for e in alerts)
