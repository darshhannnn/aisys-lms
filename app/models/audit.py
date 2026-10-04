"""Audit log ORM model.

NFR02: Every administrative and circulation action is recorded.
Logs never contain raw PII — member fields are stored as masked references.
"""
from __future__ import annotations

import uuid

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    """Immutable audit record for every state-changing action.

    Entries must NEVER be deleted or updated after creation.
    """

    __tablename__ = "audit_logs"

    # Who did it
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        # No FK constraint — audit entries must survive user deletion
        nullable=True,
        index=True,
    )
    actor_username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # What happened
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # Change details (old/new values, masked)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # actor relationship (optional — actor may have been deleted)
    actor = relationship(
        "User",
        foreign_keys=[actor_id],
        primaryjoin="AuditLog.actor_id == User.id",
        back_populates="audit_logs",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action!r} on {self.resource_type}/{self.resource_id}>"
