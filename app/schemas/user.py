"""User and authentication schemas.

Request/response models for authentication, user management, and RBAC.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


# ── Auth Schemas ───────────────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    """JWT token response (FR11)."""

    access_token: str
    token_type: str = "bearer"
    role: UserRole
    username: str


class LoginRequest(BaseModel):
    """Username/password login request."""

    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)


class SmartCardLoginRequest(BaseModel):
    """Smart-card login request (AC07)."""

    card_uid: str = Field(..., min_length=1, max_length=128)


# ── User Schemas ───────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    """Base user fields."""

    username: str = Field(..., min_length=1, max_length=64)
    email: Optional[EmailStr] = None
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.OPAC_USER
    is_active: bool = True


class UserCreate(UserBase):
    """User creation request."""

    password: str = Field(..., min_length=8)
    smart_card_id: Optional[str] = Field(None, max_length=128)
    branch_id: Optional[uuid.UUID] = None


class UserUpdate(BaseModel):
    """User update request."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    branch_id: Optional[uuid.UUID] = None


class UserResponse(UserBase):
    """User response (read-only)."""

    id: uuid.UUID
    smart_card_id: Optional[str] = None
    branch_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Branch Schemas ─────────────────────────────────────────────────────────────
class BranchBase(BaseModel):
    """Base branch fields."""

    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=16)
    address: Optional[str] = None
    is_active: bool = True


class BranchCreate(BranchBase):
    """Branch creation request."""

    pass


class BranchUpdate(BaseModel):
    """Branch update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    is_active: Optional[bool] = None


class BranchResponse(BranchBase):
    """Branch response (read-only)."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
