"""Mock SIP2 responder.

Simulates a SIP2 self-service server (e.g. a self-check kiosk backend)
for offline development and testing (FR03). Messages follow the SIP2
pattern of a two-character command code followed by field values.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


class MockSIP2Server:
    """Simulated SIP2 server.

    Supports the message pair most relevant to AC03/AC06: Checkout (11/12),
    Checkin (09/10) and Patron Status (23/24).
    """

    def __init__(self, institution_id: str = "AISYS") -> None:
        self.institution_id = institution_id
        self.online: bool = True
        self._loans: dict[str, str] = {}  # item barcode → patron identifier

    # ── Session management ────────────────────────────────────────────────

    def set_online(self, online: bool) -> None:
        """Simulate the SIP2 server going offline (NFR01 / AC09)."""
        self.online = online

    # ── SIP2 message handlers ─────────────────────────────────────────────

    async def handle_message(self, message: str) -> str:
        """Handle a raw SIP2 request message and return the response."""
        if not self.online:
            return "96ACHARGED"  # 96 = Request Sc Resend / server unavailable

        code = message[:2]
        handler = {
            "11": self._checkout,
            "09": self._checkin,
            "23": self._patron_status,
        }.get(code)
        if handler is None:
            return "96AFUnsupported message"
        return await handler(message)

    async def _checkout(self, message: str) -> str:
        """Checkout (11) → Checkout Response (12)."""
        # Fields: AO institution, AA patron, AB item
        fields = self._fields(message)
        item = fields.get("AB", "")
        patron = fields.get("AA", "")
        ok = bool(item and patron)
        if ok:
            self._loans[item] = patron
        return f"12{'1' if ok else '0'}AO{self.institution_id}|AB{item}|AF{'OK' if ok else 'Missing fields'}|"

    async def _checkin(self, message: str) -> str:
        """Checkin (09) → Checkin Response (10)."""
        fields = self._fields(message)
        item = fields.get("AB", "")
        ok = item in self._loans
        self._loans.pop(item, None)
        return f"10{'1' if ok else '0'}AO{self.institution_id}|AB{item}|AF{'OK' if ok else 'No active loan'}|"

    async def _patron_status(self, message: str) -> str:
        """Patron Status (23) → Patron Status Response (24)."""
        fields = self._fields(message)
        patron = fields.get("AA", "")
        ok = bool(patron)
        return f"24{'1' if ok else '0'}AO{self.institution_id}|AA{patron}|AF{'OK' if ok else 'Unknown patron'}|"

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _fields(message: str) -> dict[str, str]:
        """Parse ``XXvalue|`` fields out of a SIP2 message body."""
        fields: dict[str, str] = {}
        for part in message[2:].split("|"):
            if len(part) >= 2:
                fields.setdefault(part[:2], part[2:])
        return fields

    @staticmethod
    def transaction_id() -> str:
        return f"SIP2-{uuid.uuid4().hex[:12].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
