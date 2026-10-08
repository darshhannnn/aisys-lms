"""Mock NCIP 2.0 responder.

Simulates an NCIP-conformant external ILMS endpoint for offline
development and testing (FR03). The NCIPAdapter client in
``app.rfid.ncip.client`` targets this boundary during the prototype.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class NCIPResponse:
    """A simulated NCIP response message."""

    success: bool
    message: str
    transaction_id: str
    request_type: str
    detail: dict = field(default_factory=dict)


class MockNCIPResponder:
    """Simulated NCIP 2.0 endpoint.

    Supports the core circulation services used in the AC03 scenario:
    LookupItem, CheckoutItem, CheckInItem and RenewItem.
    """

    def __init__(self, agency_id: str = "AISYS_LIB") -> None:
        self.agency_id = agency_id
        self.online: bool = True
        self._known_items: dict[str, dict] = {}   # item barcode → metadata
        self._loans: dict[str, str] = {}          # item barcode → patron id

    # ── Session management ────────────────────────────────────────────────

    def set_online(self, online: bool) -> None:
        """Simulate the endpoint going offline (NFR01 / AC09)."""
        self.online = online

    def register_item(self, barcode: str, title: str = "", **meta) -> None:
        """Register an item known to the external ILMS."""
        self._known_items[barcode] = {"title": title, **meta}

    # ── NCIP services ─────────────────────────────────────────────────────

    async def lookup_item(self, barcode: str) -> NCIPResponse:
        """NCIP LookupItem service."""
        if not self.online:
            return NCIPResponse(False, "NCIP endpoint unreachable", "", "LookupItem")
        if barcode not in self._known_items:
            return NCIPResponse(False, "Unknown item", self._txn(), "LookupItem")
        return NCIPResponse(
            True,
            "Item found",
            self._txn(),
            "LookupItem",
            detail={"item": self._known_items[barcode], "agency": self.agency_id},
        )

    async def checkout_item(self, barcode: str, patron_id: str) -> NCIPResponse:
        """NCIP CheckoutItem service."""
        if not self.online:
            return NCIPResponse(False, "NCIP endpoint unreachable", "", "CheckoutItem")
        txn = self._txn()
        self._loans[barcode] = patron_id
        return NCIPResponse(True, "Checkout successful", txn, "CheckoutItem")

    async def checkin_item(self, barcode: str) -> NCIPResponse:
        """NCIP CheckInItem service."""
        if not self.online:
            return NCIPResponse(False, "NCIP endpoint unreachable", "", "CheckInItem")
        self._loans.pop(barcode, None)
        return NCIPResponse(True, "Check-in successful", self._txn(), "CheckInItem")

    async def renew_item(self, barcode: str) -> NCIPResponse:
        """NCIP RenewItem service."""
        if not self.online:
            return NCIPResponse(False, "NCIP endpoint unreachable", "", "RenewItem")
        if barcode not in self._loans:
            return NCIPResponse(False, "No active loan", self._txn(), "RenewItem")
        return NCIPResponse(True, "Renewal successful", self._txn(), "RenewItem")

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _txn() -> str:
        return f"NCIP-{uuid.uuid4().hex[:12].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
