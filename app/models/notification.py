"""Notification ORM model.

Supports email, SMS, and print notifications for circulation events,
overdue items, fines, and gate alerts (FR09, AC06).
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.member import Member


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    SMS = "sms"
    PRINT = "print"
    SYSTEM = "system"  # In-app notification


class NotificationStatus(str, enum.Enum):
    """Notification delivery status."""

    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationType(str, enum.Enum):
    """Types of notifications."""

    LOAN_DUE_REMINDER = "loan_due_reminder"
    OVERDUE_NOTICE = "overdue_notice"
    FINE_PAYMENT_REQUIRED = "fine_payment_required"
    ITEM_AVAILABLE = "item_available"
    GATE_ALERT = "gate_alert"
    CIRCULATION_BLOCKED = "circulation_blocked"
    ACCOUNT_NOTICE = "account_notice"


class Notification(Base):
    """Notification record for member communications."""

    __tablename__ = "notifications"

    # Recipient (nullable — gate alerts notify staff, not a specific member)
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), nullable=True, index=True
    )
    recipient_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipient_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Content
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel"), nullable=False
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status"),
        nullable=False,
        default=NotificationStatus.PENDING,
        index=True,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Context (links to related entities)
    related_loan_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    related_item_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    related_gate_event_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)

    # Delivery tracking
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    is_system_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification {self.notification_type.value} to {self.recipient_email or self.recipient_phone}>"
