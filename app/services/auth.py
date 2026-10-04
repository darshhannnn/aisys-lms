"""Authentication service.

Business logic for user authentication, password management, and JWT token handling.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.user import UserRepository


class AuthService:
    """Authentication business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(User, session)

    async def authenticate_user(
        self,
        username: str,
        password: str,
    ) -> User | None:
        """Authenticate user with username and password.

        Returns:
            User if authentication successful, None otherwise.
        """
        user = await self.user_repo.get_by_username(username)
        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def create_user(
        self,
        username: str,
        password: str,
        email: str | None,
        full_name: str,
        role: UserRole = UserRole.OPAC_USER,
        smart_card_id: str | None = None,
        branch_id: uuid.UUID | None = None,
    ) -> User:
        """Create a new user with hashed password."""
        hashed_pw = hash_password(password)
        from app.schemas.user import UserCreate

        user_data = UserCreate(
            username=username,
            password=hashed_pw,  # Already hashed
            email=email,
            full_name=full_name,
            role=role,
            smart_card_id=smart_card_id,
            branch_id=branch_id,
        )
        # Override password with already-hashed version
        user_dict = user_data.model_dump()
        user_dict["password"] = hashed_pw

        user = User(**user_dict)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def change_password(
        self,
        user: User,
        new_password: str,
    ) -> User:
        """Change user password."""
        user.hashed_password = hash_password(new_password)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    def generate_token(self, user: User) -> str:
        """Generate JWT access token for user."""
        return create_access_token(
            str(user.id),
            extra={"role": user.role.value, "username": user.username},
        )

    def get_token_expiry(self) -> datetime:
        """Get token expiry timestamp based on settings."""
        return datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
