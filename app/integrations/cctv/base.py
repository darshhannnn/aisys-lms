"""CCTV integration base interface.

Abstract base for CCTV/image capture systems.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class CCTVFrame:
    """CCTV frame/image data structure."""

    camera_id: str
    timestamp: str
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CCTVResult:
    """Result of CCTV capture operation."""

    success: bool
    frame: Optional[CCTVFrame] = None
    error: Optional[str] = None


class BaseCCTVProvider(ABC):
    """Abstract base for CCTV providers."""

    @abstractmethod
    async def capture_frame(self, camera_id: str) -> CCTVResult:
        """Capture a frame from a CCTV camera."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if CCTV service is available."""
        ...
