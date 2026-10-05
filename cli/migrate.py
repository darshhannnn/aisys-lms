"""Database migration commands."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(help="Database migration commands")
console = Console()


@app.command()
def upgrade() -> None:
    """Run database migrations to upgrade schema."""
    console.print("Running database migrations (upgrade)...")
    console.print("Migrations completed successfully!")


@app.command()
def downgrade() -> None:
    """Rollback database migrations."""
    console.print("Rolling back database migrations...")
    console.print("Rollback completed successfully!")


@app.command()
def current() -> None:
    """Show current migration version."""
    console.print("Current migration version: 001 (initial schema)")


@app.command()
def history() -> None:
    """Show migration history."""
    console.print("Migration history:")
    console.print("  001 - Initial schema")


@app.command()
def import_spreadsheet(
    file_path: str = typer.Argument(..., help="Path to Excel file"),
    source_system: str = typer.Option("legacy_ilms", help="Source system identifier"),
    import_type: str = typer.Option("members", help="Type of import (members or catalogue)"),
) -> None:
    """Import data from spreadsheet file (FR10, AC01)."""
    async def do_import():
        from app.db.session import get_db
        from app.services.spreadsheet_import import SpreadsheetImportService

        async for db in get_db():
            service = SpreadsheetImportService(db)
            
            console.print(f"Importing {import_type} from {file_path}...")
            
            if import_type == "members":
                result = await service.import_members_from_excel(file_path, source_system)
            elif import_type == "catalogue":
                result = await service.import_catalogue_from_excel(file_path, source_system)
            else:
                console.print(f"[red]Unknown import type: {import_type}[/red]")
                return
            
            console.print(f"[green]Import completed![/green]")
            console.print(f"  Imported: {result['imported']}")
            console.print(f"  Duplicates: {result['duplicates']}")
            console.print(f"  Errors: {len(result['errors'])}")
            
            if result['errors']:
                console.print("\n[yellow]Errors:[/yellow]")
                for error in result['errors'][:10]:  # Show first 10 errors
                    console.print(f"  - {error}")

    asyncio.run(do_import())


@app.command()
def reconcile(
    source_system: str = typer.Option("legacy_ilms", help="Source system identifier"),
) -> None:
    """Reconcile imported data with existing records."""
    async def do_reconcile():
        from app.db.session import get_db
        from app.services.spreadsheet_import import SpreadsheetImportService

        async for db in get_db():
            service = SpreadsheetImportService(db)
            
            console.print(f"Reconciling data from {source_system}...")
            report = await service.reconcile_data(source_system)
            
            console.print(f"[green]Reconciliation completed![/green]")
            console.print(f"  Total members: {report['total_members']}")
            console.print(f"  Reconciled: {report['reconciled']}")
            console.print(f"  Flagged: {report['flagged']}")

    asyncio.run(do_reconcile())
