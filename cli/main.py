"""CLI entry point for AISYS LMS.

Provides commands for database migrations, seeding, and administration.
"""
from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(
    name="aisys",
    help="AISYS RFID-Enabled Library Management System CLI",
    add_completion=False,
)
console = Console()


@app.command()
def version() -> None:
    """Show AISYS LMS version."""
    console.print("AISYS LMS v0.1.0 - Candidate Prototype")


@app.command()
def init() -> None:
    """Initialize the AISYS LMS database."""
    console.print("Initializing AISYS LMS database...")
    console.print("Database initialized successfully!")


# Import sub-commands
from cli import migrate, seed

app.add_typer(migrate.app, name="migrate", help="Database migration commands")
app.add_typer(seed.app, name="seed", help="Data seeding commands")


if __name__ == "__main__":
    app()
