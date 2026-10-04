"""Email integration base interface.

Abstract base for email service providers (SMTP, SendGrid, etc.).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmailMessage:
    """Email message data structure."""

    to: str
    subject: str
    body: str
    from_email: Optional[str] = None
    html_body: Optional[str] = None


@dataclass
class EmailResult:
    """Result of email send operation."""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class BaseEmailProvider(ABC):
    """Abstract base for email providers."""

    @abstractmethod
    async def send(self, message: EmailMessage) -> EmailResult:
        """Send an email message."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if email service is available."""
        ...
