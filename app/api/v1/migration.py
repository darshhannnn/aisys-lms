"""Data migration API endpoints.

Spreadsheet import and reconciliation for legacy ILS data (FR10, AC01).
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.dependencies import DatabaseSession, require_librarian
from app.services.spreadsheet_import import SpreadsheetImportService
from typing import Annotated

log = structlog.get_logger(__name__)
router = APIRouter()


class MigrationImportRequest(BaseModel):
    """Request to import a spreadsheet from the server filesystem."""

    file_path: str = Field(..., min_length=1, description="Absolute or relative path to .xlsx file")
    import_type: str = Field("members", pattern="^(members|catalogue)$")
    source_system: str = Field("legacy_ilms", max_length=64)


class MigrationReportRequest(BaseModel):
    """Request for a reconciliation report."""

    source_system: str = Field("legacy_ilms", max_length=64)


@router.post("/import", summary="Import a legacy spreadsheet (FR10, AC01)")
async def import_spreadsheet(
    request: MigrationImportRequest,
    db: DatabaseSession,
    current_user: Annotated[object, require_librarian],
) -> dict:
    """Import members or catalogue records from an Excel file (FR10, AC01)."""
    import os

    if not os.path.isfile(request.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    service = SpreadsheetImportService(db)
    if request.import_type == "catalogue":
        result = await service.import_catalogue_from_excel(
            request.file_path, source_system=request.source_system
        )
    else:
        result = await service.import_members_from_excel(
            request.file_path, source_system=request.source_system
        )

    log.info(
        "migration_import_completed",
        import_type=request.import_type,
        imported=result["imported"],
        duplicates=result["duplicates"],
        errors=len(result["errors"]),
    )
    return result


@router.post("/reconcile", summary="Reconcile imported data (AC01)")
async def reconcile_imported_data(
    request: MigrationReportRequest,
    db: DatabaseSession,
    current_user: Annotated[object, require_librarian],
) -> dict:
    """Reconcile imported records against the live tables (AC01)."""
    service = SpreadsheetImportService(db)
    report = await service.reconcile_data(request.source_system)

    log.info("migration_reconciliation_completed", source_system=request.source_system)
    return report
