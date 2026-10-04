"""Circulation ORM models: Loan, Renewal, Fine.

Implements:
- FR04: check-out, check-in, renewal, due-date enquiry, reference restrictions,
        member blocking, configurable fine limits, role-based rights
- AC03: auditable transaction history
- AC04: block circulation for reference item / blocked member / fine limit
"""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.member import Member
    from app.models.catalogue import Item
    from app.models.user import User


class LoanStatus(str, enum.Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"
    RENEWED = "renewed"


class FineStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    WAIVED = "waived"


class CirculationBlockReason(str, enum.Enum):
    """Why a circulation action was blocked (AC04)."""
    MEMBER_BLOCKED = "member_blocked"
    REFERENCE_ITEM = "reference_item"
    FINE_LIMIT_EXCEEDED = "fine_limit_exceeded"
    MEMBERSHIP_EXPIRED = "membership_expired"
    ITEM_NOT_AVAILABLE = "item_not_available"
    MAX_LOANS_REACHED = "max_loans_reached"


class Loan(Base):
    """A single check-out event (item lent to member).

    Each loan records the full lifecycle: issued → returned (or lost/renewed).
    Provides the auditable transaction history required by AC03.
    """

    __tablename__ = "loans"

    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    issued_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    returned_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus, name="loan_status"), nullable=False, default=LoanStatus.ACTIVE
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    renewals_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # NCIP / SIP2 transaction reference (FR03, AC03)
    protocol: Mapped[str | None] = mapped_column(String(16), nullable=True)  # "ncip" | "sip2" | "direct"
    protocol_transaction_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Block reason if the initial request was denied (AC04)
    block_reason: Mapped[CirculationBlockReason | None] = mapped_column(
        Enum(CirculationBlockReason, name="circ_block_reason"), nullable=True
    )

    # Relationships
    member: Mapped[Member] = relationship("Member", back_populates="loans")
    item: Mapped[Item] = relationship("Item", back_populates="loans")
    renewals: Mapped[list[Renewal]] = relationship("Renewal", back_populates="loan", lazy="select")
    fines: Mapped[list[Fine]] = relationship("Fine", back_populates="loan", lazy="select")

    def __repr__(self) -> str:
        return f"<Loan {self.id} status={self.status.value} due={self.due_date}>"


class Renewal(Base):
    """Records each renewal event for a loan.

    Max renewals are configurable (settings.max_renewals).
    """

    __tablename__ = "renewals"

    loan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    renewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    renewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    old_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    new_due_date: Mapped[date] = mapped_column(Date, nullable=False)

    loan: Mapped[Loan] = relationship("Loan", back_populates="renewals")


class Fine(Base):
    """A fine levied against a member for an overdue/lost item.

    Supports configurable fine limit blocking (AC04, settings.max_fine_before_block).
    """

    __tablename__ = "fines"

    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    loan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("loans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    levied_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    waived_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[FineStatus] = mapped_column(
        Enum(FineStatus, name="fine_status"), nullable=False, default=FineStatus.UNPAID
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    waive_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    member: Mapped[Member] = relationship("Member", back_populates="fines")
    loan: Mapped[Loan | None] = relationship("Loan", back_populates="fines")

    def __repr__(self) -> str:
        return f"<Fine {self.amount} status={self.status.value}>"
