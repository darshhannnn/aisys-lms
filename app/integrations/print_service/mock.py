"""Mock print service provider.

Simulates print jobs for offline/development environments.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from app.integrations.print_service.base import BasePrintProvider, PrintJob, PrintResult


class MockPrintProvider(BasePrintProvider):
    """Mock print provider for development/testing.

    Logs print jobs instead of actually printing.
    """

    def __init__(self):
        self.print_jobs: list[PrintJob] = []

    async def print(self, job: PrintJob) -> PrintResult:
        """Simulate submitting a print job (logs it instead)."""
        await asyncio.sleep(0.2)  # Simulate print queue latency

        # Store job for inspection
        self.print_jobs.append(job)

        # In a real implementation, this would submit to a print queue
        print(f"[MOCK PRINT] Printer: {job.printer_id}, Title: {job.title or 'Untitled'}")

        return PrintResult(
            success=True,
            job_id=f"mock_print_{id(job)}",
        )

    async def is_available(self) -> bool:
        """Mock print service is always available."""
        return True

    def get_print_jobs(self) -> list[PrintJob]:
        """Get all print jobs submitted through this mock provider."""
        return self.print_jobs.copy()

    def clear(self) -> None:
        """Clear print jobs history."""
        self.print_jobs.clear()
