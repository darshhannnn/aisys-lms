"""User and Role ORM models.

Supports:
- Username/password (library staff)
- Smart-card login (via mock credential provider — AC07)
- Role-based permissions (FR11, AC07)
- Full audit trail on auth events
"""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.audit import AuditLog
    from app.models.circulation import Loan


class UserRole(str, enum.Enum):
    """Role-based access control roles (FR11, AC07)."""

    SUPER_ADMIN = "super_admin"
    LIBRARIAN = "librarian"
    CIRCULATION_STAFF = "circulation_staff"
    CATALOGUER = "cataloguer"
    REPORTS_VIEWER = "reports_viewer"
    OPAC_USER = "opac_user"      # Public OPAC self-service


class User(Base):
    """Library staff and OPAC user account."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Smart-card support (AC07) — external credential provider token
    smart_card_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    smart_card_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.OPAC_USER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Branch / department this user belongs to (multi-branch support)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    audit_logs: Mapped[list[AuditLog]] = relationship("AuditLog", back_populates="actor", lazy="select")

    def __repr__(self) -> str:
        return f"<User {self.username!r} role={self.role.value}>"


class Branch(Base):
    """Library branch (supports multi-branch deployments)."""

    __tablename__ = "branches"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list[User]] = relationship("User", backref="branch", lazy="select")
