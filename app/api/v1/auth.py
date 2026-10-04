"""Auth API — username/password login and smart-card login (AC07)."""
from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.rfid.adapters.mock_smartcard import MockSmartCardAdapter

log = structlog.get_logger(__name__)
router = APIRouter()

_smartcard_adapter = MockSmartCardAdapter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class SmartCardLoginRequest(BaseModel):
    card_uid: str


@router.post("/login", response_model=TokenResponse, summary="Username/password login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with username + password and return a JWT."""
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(form_data.password, user.hashed_password):
        log.warning("login_failed", username=form_data.username[:2] + "***")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = create_access_token(str(user.id), extra={"role": user.role.value, "username": user.username})
    log.info("login_success", username=user.username, role=user.role.value)
    return TokenResponse(access_token=token, role=user.role.value, username=user.username)


@router.post("/smartcard-login", response_model=TokenResponse, summary="Smart-card login (AC07)")
async def smartcard_login(
    body: SmartCardLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate via a smart card and return a JWT (AC07).

    The card UID is validated against the mock credential provider.
    In production this maps to the institutional LDAP/smart-card service.
    """
    principal = await _smartcard_adapter.authenticate_card(body.card_uid)
    if not principal:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Card not recognised")

    # Look up or lazily create the user record
    result = await db.execute(select(User).where(User.smart_card_id == body.card_uid))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Card recognised but no linked staff account found",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = create_access_token(str(user.id), extra={"role": user.role.value, "username": user.username})
    log.info("smartcard_login_success", username=user.username, role=user.role.value)
    return TokenResponse(access_token=token, role=user.role.value, username=user.username)
