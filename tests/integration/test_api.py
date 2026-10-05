"""Integration tests for API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_login(self, client: AsyncClient):
        """Test login endpoint."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin"},
        )
        # May fail if user doesn't exist, but endpoint should respond
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_catalogue_search(self, client: AsyncClient):
        """Test catalogue search endpoint."""
        response = await client.get("/api/v1/catalogue/search?query=test")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_dashboard_stats(self, client: AsyncClient):
        """Test dashboard statistics endpoint."""
        response = await client.get("/api/v1/reports/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data
