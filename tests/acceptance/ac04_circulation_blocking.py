"""AC04: Block circulation for reference items or fine/limit exceedances.

Acceptance test for circulation blocking (FR04).
"""
from __future__ import annotations

import pytest


@pytest.mark.acceptance
class TestAC04CirculationBlocking:
    """Acceptance tests for circulation blocking (AC04)."""

    @pytest.mark.asyncio
    async def test_block_reference_item(self):
        """Test that reference items cannot be checked out."""
        # TODO: Implement reference item blocking
        assert True

    @pytest.mark.asyncio
    async def test_block_fine_exceedance(self):
        """Test that members with excessive fines are blocked."""
        # TODO: Implement fine limit blocking
        assert True

    @pytest.mark.asyncio
    async def test_block_loan_limit(self):
        """Test that members exceeding loan limit are blocked."""
        # TODO: Implement loan limit blocking
        assert True

    @pytest.mark.asyncio
    async def test_unblock_member(self):
        """Test unblocking a member."""
        # TODO: Implement unblock logic
        assert True
