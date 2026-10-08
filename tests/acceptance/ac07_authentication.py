"""AC07: Staff smart-card login mock and RBAC enforcement.

Acceptance test for authentication and RBAC (FR11).
"""
from __future__ import annotations

import uuid

import pytest

from app.models.user import UserRole
from app.rfid.adapters.mock_smartcard import MockSmartCardAdapter
from app.services.auth import AuthService


@pytest.mark.acceptance
class TestAC07Authentication:
    """Acceptance tests for authentication and RBAC (AC07)."""

    async def _make_user(self, db_session, role: UserRole, with_card: str | None = None):
        service = AuthService(db_session)
        suffix = uuid.uuid4().hex[:8]
        return await service.create_user(
            username=f"ac07-{role.value}-{suffix}",
            password="Str0ng!Passphrase",
            email=f"ac07-{suffix}@example.edu",
            full_name=f"AC07 {role.value}",
            role=role,
            smart_card_id=with_card,
        )

    @pytest.mark.asyncio
    async def test_smart_card_login(self, client, db_session):
        """A registered smart card maps to a staff account and returns a JWT."""
        card_uid = f"CARD-AC07-{uuid.uuid4().hex[:10].upper()}"
        MockSmartCardAdapter().register_card(
            card_uid, username=f"ac07card-{uuid.uuid4().hex[:6]}", role="librarian",
            full_name="AC07 Card Holder",
        )
        user = await self._make_user(db_session, UserRole.LIBRARIAN, with_card=card_uid)
        assert user.smart_card_id == card_uid

        response = await client.post("/api/v1/auth/smartcard-login", json={"card_uid": card_uid})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["access_token"]
        assert data["role"] == "librarian"

    @pytest.mark.asyncio
    async def test_username_password_login(self, client, db_session):
        """Username/password login returns a JWT; bad passwords are rejected."""
        user = await self._make_user(db_session, UserRole.CIRCULATION_STAFF)

        ok = await client.post(
            "/api/v1/auth/login",
            data={"username": user.username, "password": "Str0ng!Passphrase"},
        )
        assert ok.status_code == 200, ok.text
        assert ok.json()["access_token"]

        bad = await client.post(
            "/api/v1/auth/login",
            data={"username": user.username, "password": "wrong-password"},
        )
        assert bad.status_code == 401

    @pytest.mark.asyncio
    async def test_rbac_enforcement(self, client, db_session):
        """A librarian token passes RBAC; an OPAC user's token is refused."""
        librarian = await self._make_user(db_session, UserRole.LIBRARIAN)
        opac = await self._make_user(db_session, UserRole.OPAC_USER)
        auth_service = AuthService(db_session)

        librarian_token = auth_service.generate_token(librarian)
        opac_token = auth_service.generate_token(opac)

        ok = await client.post(
            "/api/v1/notifications/",
            json={
                "channel": "email",
                "notification_type": "account_notice",
                "subject": "AC07 RBAC",
                "body": "Librarian action permitted",
            },
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert ok.status_code == 200, ok.text

        denied = await client.post(
            "/api/v1/notifications/",
            json={
                "channel": "email",
                "notification_type": "account_notice",
                "subject": "AC07 RBAC",
                "body": "OPAC user must not do staff work",
            },
            headers={"Authorization": f"Bearer {opac_token}"},
        )
        assert denied.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthorized_access_blocking(self, client):
        """Requests without a token never reach staff endpoints."""
        no_token = await client.post(
            "/api/v1/notifications/",
            json={
                "channel": "email",
                "notification_type": "account_notice",
                "subject": "AC07 anon",
                "body": "Anonymous request",
            },
        )
        assert no_token.status_code in (401, 403)

        fake = await client.post(
            "/api/v1/notifications/send-overdue-reminders",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert fake.status_code in (401, 403)
