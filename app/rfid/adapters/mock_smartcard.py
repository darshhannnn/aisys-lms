"""Mock smart-card credential provider (AC07).

Simulates a smart-card authentication flow without real hardware.
Returns a principal object that maps to a User record and enforces RBAC.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass

from app.rfid.adapters.base import BaseRfidAdapter, ReadResult, TagReadEvent, WriteResult

log = structlog.get_logger(__name__)

# ── Synthetic smart-card registry ─────────────────────────────────────────────
# These are synthetic credentials only. No real institutional data.
_MOCK_CARDS: dict[str, dict] = {
    "CARD-ADMIN-0001": {"username": "admin", "role": "super_admin", "full_name": "Alice Admin"},
    "CARD-LIB-0002":   {"username": "librarian1", "role": "librarian", "full_name": "Bob Librarian"},
    "CARD-CIRC-0003":  {"username": "circ1", "role": "circulation_staff", "full_name": "Carol Circulation"},
}


@dataclass
class SmartCardPrincipal:
    """The authenticated identity returned after card validation (AC07)."""

    card_uid: str
    username: str
    role: str
    full_name: str
    authenticated: bool = True


class MockSmartCardAdapter(BaseRfidAdapter):
    """Mock smart-card reader that authenticates against the synthetic registry.

    In production this adapter boundary would be replaced with a real
    credential-provider integration (e.g., LDAP smart-card middleware).
    """

    adapter_id = "mock_smartcard"

    async def read_tag(self, timeout_s: float = 10.0) -> TagReadEvent:
        """Not used directly — use authenticate_card() instead."""
        return TagReadEvent(tag_uid="", reader_id=self.adapter_id, result=ReadResult.NO_TAG)

    async def write_tag(self, tag_uid: str, data: dict) -> WriteResult:
        return WriteResult(success=False, tag_uid=tag_uid, error="Smart-card adapter is read-only")

    async def is_online(self) -> bool:
        return True  # mock always online

    async def authenticate_card(self, card_uid: str) -> SmartCardPrincipal | None:
        """Validate a card UID and return the principal, or None if unknown (AC07).

        In a real deployment, this would call the institutional credential provider.
        """
        card_data = _MOCK_CARDS.get(card_uid)
        if card_data is None:
            log.warning("smartcard_auth_failed", card_uid=card_uid[:4] + "***")
            return None

        principal = SmartCardPrincipal(
            card_uid=card_uid,
            username=card_data["username"],
            role=card_data["role"],
            full_name=card_data["full_name"],
        )
        log.info("smartcard_auth_success", username=principal.username, role=principal.role)
        return principal

    def register_card(self, card_uid: str, username: str, role: str, full_name: str) -> None:
        """Register a new synthetic card (for testing only)."""
        _MOCK_CARDS[card_uid] = {"username": username, "role": role, "full_name": full_name}
        log.info("smartcard_registered", card_uid=card_uid[:4] + "***", username=username)
