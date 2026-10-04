"""Mock email provider.

Simulates email sending for offline/development environments.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from app.integrations.email.base import BaseEmailProvider, EmailMessage, EmailResult


class MockEmailProvider(BaseEmailProvider):
    """Mock email provider for development/testing.

    Logs email messages instead of actually sending them.
    """

    def __init__(self):
        self.sent_messages: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> EmailResult:
        """Simulate sending an email (logs it instead)."""
        await asyncio.sleep(0.1)  # Simulate network latency

        # Store message for inspection
        self.sent_messages.append(message)

        # In a real implementation, this would use SMTP or an API
        print(f"[MOCK EMAIL] To: {message.to}, Subject: {message.subject}")

        return EmailResult(
            success=True,
            message_id=f"mock_{id(message)}",
        )

    async def is_available(self) -> bool:
        """Mock email is always available."""
        return True

    def get_sent_messages(self) -> list[EmailMessage]:
        """Get all messages sent through this mock provider."""
        return self.sent_messages.copy()

    def clear(self) -> None:
        """Clear sent messages history."""
        self.sent_messages.clear()
