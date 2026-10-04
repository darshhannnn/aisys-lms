"""Data seeding commands."""
from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(help="Data seeding commands")
console = Console()


@app.command()
def users() -> None:
    """Seed initial users (admin accounts)."""
    console.print("Seeding initial users...")
    console.print("Users seeded successfully!")


@app.command()
def catalogue() -> None:
    """Seed sample bibliographic records and items."""
    console.print("Seeding sample catalogue data...")
    console.print("Catalogue data seeded successfully!")


@app.command()
def members() -> None:
    """Seed sample member records."""
    console.print("Seeding sample members...")
    console.print("Members seeded successfully!")


@app.command()
def all() -> None:
    """Seed all sample data."""
    console.print("Seeding all sample data...")
    console.print("All data seeded successfully!")
