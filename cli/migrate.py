"""Database migration commands.

Real Alembic operations plus backup/restore for the offline lifecycle
(FR12, AC09, AC10).
"""
from __future__ import annotations

import asyncio
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import typer
from alembic import command
from alembic.config import Config
from rich.console import Console

app = typer.Typer(help="Database migration commands")
console = Console()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"


def _alembic_config() -> Config:
    """Build the Alembic config for the project."""
    cfg = Config(PROJECT_ROOT / "alembic.ini")
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    return cfg


def _sqlite_path(db_url: str) -> str | None:
    """Extract the filesystem path from a SQLite URL, if it is one."""
    if not db_url.startswith("sqlite"):
        return None
    path = db_url.split("///", 1)[-1]
    return os.path.abspath(path)


@app.command()
def upgrade(revision: str = typer.Option("head", help="Target revision")) -> None:
    """Run database migrations to upgrade schema."""
    console.print(f"Running database migrations (upgrade to {revision})...")
    command.upgrade(_alembic_config(), revision)
    console.print("[green]Migrations completed successfully![/green]")


@app.command()
def downgrade(
    steps: int = typer.Option(1, help="Number of revisions to roll back"),
) -> None:
    """Rollback database migrations."""
    console.print(f"Rolling back {steps} revision(s)...")
    command.downgrade(_alembic_config(), f"-{steps}")
    console.print("[green]Rollback completed successfully![/green]")


@app.command()
def current() -> None:
    """Show current migration version."""
    command.current(_alembic_config())


@app.command()
def history() -> None:
    """Show migration history."""
    command.history(_alembic_config())


@app.command()
def backup(
    destination: str = typer.Option(None, help="Backup file path (default: data/backups/)"),
) -> str:
    """Back up the database (SQLite file copy; Postgres: use pg_dump)."""
    from app.core.config import settings

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_path = _sqlite_path(settings.database_url_sync)

    if db_path is None:
        console.print("[red]Automatic backup supports SQLite only.[/red]")
        console.print("For PostgreSQL use: pg_dump <database> > backup.sql")
        raise typer.Exit(code=1)

    if not os.path.exists(db_path):
        console.print(f"[red]Database file not found: {db_path}[/red]")
        raise typer.Exit(code=1)

    dest = Path(destination) if destination else BACKUP_DIR / f"aisys_lms_{timestamp}.db"
    shutil.copy2(db_path, dest)

    # Verify the backup is a readable, intact SQLite database
    with sqlite3.connect(dest) as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        console.print(f"[red]Backup integrity check FAILED: {integrity}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]Backup created:[/green] {dest} (integrity: ok)")
    return str(dest)


@app.command()
def restore(
    backup_file: str = typer.Argument(..., help="Path to the backup file to restore"),
    force: bool = typer.Option(False, "--force", help="Overwrite the live database without prompting"),
) -> None:
    """Restore the database from a backup file (AC10)."""
    from app.core.config import settings

    src = Path(backup_file)
    if not src.is_file():
        console.print(f"[red]Backup file not found: {src}[/red]")
        raise typer.Exit(code=1)

    # Verify backup integrity before touching the live database
    with sqlite3.connect(src) as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        console.print(f"[red]Backup integrity check FAILED: {integrity} — aborting.[/red]")
        raise typer.Exit(code=1)

    db_path = _sqlite_path(settings.database_url_sync)
    if db_path is None:
        console.print("[red]Automatic restore supports SQLite only.[/red]")
        raise typer.Exit(code=1)

    if not force:
        confirm = typer.confirm(f"Overwrite {db_path} with {src}?")
        if not confirm:
            console.print("Restore cancelled.")
            raise typer.Exit()

    shutil.copy2(src, db_path)

    # Validate the restored database
    with sqlite3.connect(db_path) as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if integrity != "ok":
        console.print("[red]Restored database failed integrity check![/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]Database restored from {src}[/green]")
    console.print(f"  Tables present: {len(tables - {'sqlite_sequence'})}")
    console.print("  Integrity: ok")


@app.command()
def import_spreadsheet(
    file_path: str = typer.Argument(..., help="Path to Excel file"),
    source_system: str = typer.Option("legacy_ilms", help="Source system identifier"),
    import_type: str = typer.Option("members", help="Type of import (members or catalogue)"),
) -> None:
    """Import data from spreadsheet file (FR10, AC01)."""
    async def do_import():
        from app.db.session import get_session_factory
        from app.services.spreadsheet_import import SpreadsheetImportService

        session_factory = get_session_factory()
        async with session_factory() as db:
            service = SpreadsheetImportService(db)

            console.print(f"Importing {import_type} from {file_path}...")

            if import_type == "members":
                result = await service.import_members_from_excel(file_path, source_system)
            elif import_type == "catalogue":
                result = await service.import_catalogue_from_excel(file_path, source_system)
            else:
                console.print(f"[red]Unknown import type: {import_type}[/red]")
                return

            await db.commit()

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
        from app.db.session import get_session_factory
        from app.services.spreadsheet_import import SpreadsheetImportService

        session_factory = get_session_factory()
        async with session_factory() as db:
            service = SpreadsheetImportService(db)

            console.print(f"Reconciling data from {source_system}...")
            report = await service.reconcile_data(source_system)

            console.print(f"[green]Reconciliation completed![/green]")
            console.print(f"  Total members: {report['total_members']}")
            console.print(f"  Reconciled: {report['reconciled']}")
            console.print(f"  Flagged: {report['flagged']}")

    asyncio.run(do_reconcile())
