"""SQLAlchemy async engine and declarative base."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool
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
    """Build and return an async SQLAlchemy engine.

    Pool tuning only applies to server-style backends (PostgreSQL);
    SQLite uses its own pooling, and in-memory SQLite needs a single
    shared connection so all sessions see the same database.
    """
    resolved = url or settings.database_url
    kwargs: dict[str, Any] = {"echo": settings.debug, "future": True}

    if resolved.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in resolved:
            kwargs["poolclass"] = StaticPool
    else:
        kwargs["pool_size"] = settings.db_pool_size
        kwargs["max_overflow"] = settings.db_max_overflow

    return create_async_engine(resolved, **kwargs)


_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Return the shared engine, creating it on first use."""
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def __getattr__(name: str) -> Any:
    # Keep ``from app.db.base import engine`` working while deferring
    # engine construction (and driver imports) until actually needed.
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
