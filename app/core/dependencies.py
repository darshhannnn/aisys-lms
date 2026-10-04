"""FastAPI dependency injection helpers.

Provides reusable dependencies for authentication, database sessions,
and other common request-scoped resources.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.db.session import get_db
from app.models.user import User, UserRole

# ── Database Session ──────────────────────────────────────────────────────────
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


# ── Authentication Dependencies ──────────────────────────────────────────────
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DatabaseSession,
) -> User:
    """Extract and validate the current user from JWT token.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    # Look up user in database
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure the current user is active (redundant with get_current_user but explicit)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


# ── Role-Based Access Control (RBAC) Dependencies ─────────────────────────────
async def require_role(*allowed_roles: UserRole) -> User:
    """Dependency factory for role-based access control.

    Usage:
        current_admin = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.LIBRARIAN))
    """
    async def role_checker(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker


# ── Pre-defined role dependencies ───────────────────────────────────────────────
require_admin = Depends(require_role(UserRole.SUPER_ADMIN))
require_librarian = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.LIBRARIAN))
require_circulation_staff = Depends(
    require_role(UserRole.SUPER_ADMIN, UserRole.LIBRARIAN, UserRole.CIRCULATION_STAFF)
)
require_cataloguer = Depends(
    require_role(UserRole.SUPER_ADMIN, UserRole.LIBRARIAN, UserRole.CATALOGUER)
)
require_reports_viewer = Depends(
    require_role(
        UserRole.SUPER_ADMIN,
        UserRole.LIBRARIAN,
        UserRole.REPORTS_VIEWER,
    )
)
