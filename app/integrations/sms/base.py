"""SMS integration base interface.

Abstract base for SMS service providers (Twilio, etc.).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SMSMessage:
    """SMS message data structure."""

    to: str
    body: str
    from_number: Optional[str] = None


@dataclass
class SMSResult:
    """Result of SMS send operation."""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class BaseSMSProvider(ABC):
    """Abstract base for SMS providers."""

    @abstractmethod
    async def send(self, message: SMSMessage) -> SMSResult:
        """Send an SMS message."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if SMS service is available."""
        ...
