"""User repository.

Data access layer for User and Branch models.
"""
from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.models.user import User, Branch, UserRole
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate, BranchCreate, BranchUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for User model."""

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.get_by_field("username", username)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.get_by_field("email", email)

    async def get_by_smart_card_id(self, smart_card_id: str) -> Optional[User]:
        """Get user by smart card ID."""
        return await self.get_by_field("smart_card_id", smart_card_id)

    async def get_by_role(
        self,
        role: UserRole,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """Get users by role."""
        result = await self.session.execute(
            select(User)
            .where(User.role == role)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """Get active users only."""
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class BranchRepository(BaseRepository[Branch, BranchCreate, BranchUpdate]):
    """Repository for Branch model."""

    async def get_by_code(self, code: str) -> Optional[Branch]:
        """Get branch by code."""
        return await self.get_by_field("code", code)

    async def get_active_branches(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Branch]:
        """Get active branches only."""
        result = await self.session.execute(
            select(Branch)
            .where(Branch.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
