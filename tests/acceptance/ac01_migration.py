"""AC01: Spreadsheet import, valid records migrated, duplicate identification.

Acceptance test for data migration from spreadsheet files (FR10, NFR01).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.spreadsheet_import import SpreadsheetImportService

SYNTHETIC_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


@pytest.mark.acceptance
class TestAC01Migration:
    """Acceptance tests for spreadsheet migration (AC01)."""

    @pytest.mark.asyncio
    async def test_spreadsheet_import(self, db_session):
        """Valid spreadsheet rows are imported into the live tables."""
        service = SpreadsheetImportService(db_session)

        members = await service.import_members_from_excel(
            str(SYNTHETIC_DIR / "synthetic_members.xlsx"), source_system="ac01_legacy"
        )
        catalogue = await service.import_catalogue_from_excel(
            str(SYNTHETIC_DIR / "synthetic_catalogue.xlsx"), source_system="ac01_legacy"
        )

        assert members["imported"] == 10, f"expected 10 members, got {members}"
        assert members["errors"] == []
        assert catalogue["imported"] == 10, f"expected 10 books, got {catalogue}"
        assert catalogue["errors"] == []

    @pytest.mark.asyncio
    async def test_duplicate_identification(self, db_session):
        """Re-importing the same spreadsheet identifies duplicates, not new rows."""
        service = SpreadsheetImportService(db_session)

        await service.import_members_from_excel(
            str(SYNTHETIC_DIR / "synthetic_members.xlsx"), source_system="ac01_dup"
        )
        second = await service.import_members_from_excel(
            str(SYNTHETIC_DIR / "synthetic_members.xlsx"), source_system="ac01_dup"
        )
        assert second["imported"] == 0
        assert second["duplicates"] == 11  # 10 re-imports + the file's own duplicate row

        catalogue_first = await service.import_catalogue_from_excel(
            str(SYNTHETIC_DIR / "synthetic_catalogue.xlsx"), source_system="ac01_dup"
        )
        assert catalogue_first["imported"] == 10
        assert catalogue_first["duplicates"] == 1  # the file's own embedded duplicate row

        catalogue_second = await service.import_catalogue_from_excel(
            str(SYNTHETIC_DIR / "synthetic_catalogue.xlsx"), source_system="ac01_dup"
        )
        assert catalogue_second["imported"] == 0
        assert catalogue_second["duplicates"] == 11  # 10 re-imports + the embedded duplicate row

    @pytest.mark.asyncio
    async def test_data_reconciliation(self, db_session):
        """Reconciliation reports every imported member as reconciled or flagged."""
        service = SpreadsheetImportService(db_session)

        await service.import_members_from_excel(
            str(SYNTHETIC_DIR / "synthetic_members.xlsx"), source_system="ac01_recon"
        )
        report = await service.reconcile_data("ac01_recon")

        assert report["source_system"] == "ac01_recon"
        assert report["total_members"] == 10
        assert report["reconciled"] + report["flagged"] == report["total_members"]
        assert report["reconciled"] == 10  # all synthetic members have contact info

    @pytest.mark.asyncio
    async def test_source_database_untampered(self, db_session):
        """NFR01: a failed/duplicate import never mutates existing records."""
        service = SpreadsheetImportService(db_session)

        await service.import_members_from_excel(
            str(SYNTHETIC_DIR / "synthetic_members.xlsx"), source_system="ac01_nfr01"
        )
        original = await service.member_repo.get_by_member_number("MEM-000003")
        assert original is not None
        assert original.full_name == "Rohan Iyer"

        # The duplicate row for MEM-000001 must not overwrite the original
        member = await service.member_repo.get_by_member_number("MEM-000001")
        assert member.full_name == "Aarav Sharma"
        assert member.email == "aarav.sharma@example.edu"
