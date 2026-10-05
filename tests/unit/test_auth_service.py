"""Unit tests for authentication service."""
from __future__ import annotations

import pytest
from app.services.auth import AuthService
from app.models.user import User, UserRole


@pytest.mark.unit
class TestAuthService:
    """Unit tests for AuthService."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test user creation."""
        service = AuthService(db_session)
        user = await service.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.LIBRARIAN,
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.LIBRARIAN
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session):
        """Test successful user authentication."""
        service = AuthService(db_session)
        await service.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            full_name="Test User",
        )
        user = await service.authenticate_user("testuser", "testpass123")
        assert user is not None
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_authenticate_user_failure(self, db_session):
        """Test failed user authentication."""
        service = AuthService(db_session)
        await service.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            full_name="Test User",
        )
        user = await service.authenticate_user("testuser", "wrongpassword")
        assert user is None

    @pytest.mark.asyncio
    async def test_generate_token(self, db_session):
        """Test JWT token generation."""
        service = AuthService(db_session)
        user = await service.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            full_name="Test User",
        )
        token = service.generate_token(user)
        assert token is not None
        assert isinstance(token, str)
