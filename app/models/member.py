"""Member ORM model.

Implements FR04: member blocking, patron-card personalisation.
Supports configurable fine limit check (AC04).
"""
from __future__ import annotations

import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.circulation import Loan, Fine
    from app.models.notification import Notification


class MemberCategory(str, enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    STAFF = "staff"
    EXTERNAL = "external"
    HONORARY = "honorary"


class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"         # FR04: member blocking
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Member(Base):
    """Library member (patron) record.

    PII fields (email, phone, national_id) MUST be masked in logs.
    All data used during development is synthetic.
    """

    __tablename__ = "members"

    # Identity
    member_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    national_id: Mapped[str | None] = mapped_column(String(64), nullable=True)  # masked in logs

    # Patron card personalisation (FR04)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    patron_card_barcode: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)

    # Category / status
    category: Mapped[MemberCategory] = mapped_column(
        Enum(MemberCategory, name="member_category"),
        nullable=False,
        default=MemberCategory.STUDENT,
    )
    status: Mapped[MemberStatus] = mapped_column(
        Enum(MemberStatus, name="member_status"),
        nullable=False,
        default=MemberStatus.ACTIVE,
    )

    # Membership validity
    membership_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    membership_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Block reason (FR04)
    block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocked_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Accumulated fines (denormalised for fast blocking checks)
    outstanding_fine: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)

    # Notification preferences
    notify_email: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_sms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_print: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Source (migration)
    source_system: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # Relationships
    loans: Mapped[list[Loan]] = relationship("Loan", back_populates="member", lazy="select")
    fines: Mapped[list[Fine]] = relationship("Fine", back_populates="member", lazy="select")
    notifications: Mapped[list[Notification]] = relationship("Notification", back_populates="member", lazy="select")

    def __repr__(self) -> str:
        return f"<Member {self.member_number!r} status={self.status.value}>"

    @property
    def is_blocked(self) -> bool:
        """True if the member cannot borrow (FR04, AC04)."""
        return self.status == MemberStatus.BLOCKED
