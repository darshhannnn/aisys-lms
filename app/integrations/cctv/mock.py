"""Mock CCTV provider.

Simulates CCTV image capture for offline/development environments.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.integrations.cctv.base import BaseCCTVProvider, CCTVFrame, CCTVResult


class MockCCTVProvider(BaseCCTVProvider):
    """Mock CCTV provider for development/testing.

    Simulates image capture without actual camera hardware.
    """

    def __init__(self):
        self.captured_frames: list[CCTVFrame] = []

    async def capture_frame(self, camera_id: str) -> CCTVResult:
        """Simulate capturing a frame (generates a mock URL)."""
        await asyncio.sleep(0.3)  # Simulate camera latency

        # Generate mock frame
        frame = CCTVFrame(
            camera_id=camera_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            image_url=f"mock_captures/{camera_id}_{datetime.now(timezone.utc).timestamp()}.jpg",
        )

        # Store frame for inspection
        self.captured_frames.append(frame)

        # In a real implementation, this would capture from actual CCTV
        print(f"[MOCK CCTV] Camera: {camera_id}, Frame captured")

        return CCTVResult(
            success=True,
            frame=frame,
        )

    async def is_available(self) -> bool:
        """Mock CCTV is always available."""
        return True

    def get_captured_frames(self) -> list[CCTVFrame]:
        """Get all frames captured through this mock provider."""
        return self.captured_frames.copy()

    def clear(self) -> None:
        """Clear captured frames history."""
        self.captured_frames.clear()
