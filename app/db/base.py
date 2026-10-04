"""SQLAlchemy async engine and declarative base."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column
from sqlalchemy import DateTime, func
from datetime import datetime
import uuid

from app.core.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    """All ORM models inherit from this base.

    Provides:
    - ``id``        — UUID primary key
    - ``created_at`` — auto-set on INSERT
    - ``updated_at`` — auto-updated on UPDATE
    """

    id: MappedColumn[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    created_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def build_engine(url: str | None = None) -> AsyncEngine:
    """Build and return an async SQLAlchemy engine."""
    return create_async_engine(
        url or settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=settings.debug,
        future=True,
    )


engine: AsyncEngine = build_engine()
