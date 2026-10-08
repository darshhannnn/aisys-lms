"""Notification schemas.

Request/response models for email, SMS, and print notifications.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.notification import NotificationChannel, NotificationStatus, NotificationType


# ── Notification Schemas ───────────────────────────────────────────────────────
class NotificationBase(BaseModel):
    """Base notification fields."""

    member_id: Optional[uuid.UUID] = None
    channel: NotificationChannel
    notification_type: NotificationType
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)


class NotificationCreate(NotificationBase):
    """Notification creation request."""

    recipient_email: Optional[str] = Field(None, max_length=255)
    recipient_phone: Optional[str] = Field(None, max_length=32)
    related_loan_id: Optional[uuid.UUID] = None
    related_item_id: Optional[uuid.UUID] = None
    related_gate_event_id: Optional[uuid.UUID] = None
    scheduled_at: Optional[datetime] = None
    notification_metadata: Optional[dict] = None


class NotificationUpdate(BaseModel):
    """Notification update request."""

    status: Optional[NotificationStatus] = None
    scheduled_at: Optional[datetime] = None
    error_message: Optional[str] = Field(None, max_length=1000)


class NotificationResponse(NotificationBase):
    """Notification response (read-only)."""

    id: uuid.UUID
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    status: NotificationStatus
    related_loan_id: Optional[uuid.UUID] = None
    related_item_id: Optional[uuid.UUID] = None
    related_gate_event_id: Optional[uuid.UUID] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivery_attempts: int = 0
    error_message: Optional[str] = None
    is_system_generated: bool = True
    notification_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Notification Template Schemas ──────────────────────────────────────────────
class NotificationTemplateRequest(BaseModel):
    """Request to generate a notification from a template."""

    notification_type: NotificationType
    member_id: Optional[uuid.UUID] = None
    context: dict = Field(default_factory=dict)  # Variables for template rendering


class BulkNotificationRequest(BaseModel):
    """Request to send bulk notifications."""

    notification_type: NotificationType
    channel: NotificationChannel
    member_ids: list[uuid.UUID] = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=255)
    body_template: str = Field(..., min_length=1)
    context: dict = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None


class BulkNotificationResponse(BaseModel):
    """Bulk notification response."""

    total_requested: int
    created_count: int
    failed_count: int
    notification_ids: list[uuid.UUID]
