"""Mock SMS provider.

Simulates SMS sending for offline/development environments.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from app.integrations.sms.base import BaseSMSProvider, SMSMessage, SMSResult


class MockSMSProvider(BaseSMSProvider):
    """Mock SMS provider for development/testing.

    Logs SMS messages instead of actually sending them.
    """

    def __init__(self):
        self.sent_messages: list[SMSMessage] = []

    async def send(self, message: SMSMessage) -> SMSResult:
        """Simulate sending an SMS (logs it instead)."""
        await asyncio.sleep(0.1)  # Simulate network latency

        # Store message for inspection
        self.sent_messages.append(message)

        # In a real implementation, this would use Twilio or similar
        print(f"[MOCK SMS] To: {message.to}, Body: {message.body[:50]}...")

        return SMSResult(
            success=True,
            message_id=f"mock_{id(message)}",
        )

    async def is_available(self) -> bool:
        """Mock SMS is always available."""
        return True

    def get_sent_messages(self) -> list[SMSMessage]:
        """Get all messages sent through this mock provider."""
        return self.sent_messages.copy()

    def clear(self) -> None:
        """Clear sent messages history."""
        self.sent_messages.clear()
