"""Print service integration base interface.

Abstract base for print service providers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PrintJob:
    """Print job data structure."""

    printer_id: str
    content: str
    copies: int = 1
    title: Optional[str] = None


@dataclass
class PrintResult:
    """Result of print job."""

    success: bool
    job_id: Optional[str] = None
    error: Optional[str] = None


class BasePrintProvider(ABC):
    """Abstract base for print providers."""

    @abstractmethod
    async def print(self, job: PrintJob) -> PrintResult:
        """Submit a print job."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if print service is available."""
        ...
