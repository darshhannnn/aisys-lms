"""AC09: Offline installation and update simulation.

Acceptance test for the offline deployment lifecycle (FR12).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _alembic_config(db_url: str) -> Config:
    cfg = Config(PROJECT_ROOT / "alembic.ini")
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _table_names(db_file: Path) -> set[str]:
    with sqlite3.connect(db_file) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {name for (name,) in rows} - {"alembic_version", "sqlite_sequence"}


@pytest.mark.acceptance
class TestAC09OfflineDeployment:
    """Acceptance tests for offline installation and updates (AC09)."""

    def test_offline_installation_artifacts(self):
        """The offline package ships an install script, compose file and pinned deps."""
        install_script = PROJECT_ROOT / "install.bat"
        compose = PROJECT_ROOT / "docker-compose.yml"
        pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        assert install_script.is_file(), "install.bat missing from offline package"
        script = install_script.read_text(encoding="utf-8")
        # Installs without internet: venv + local deps, no network downloads required
        assert "python -m venv" in script
        assert compose.is_file(), "docker-compose.yml missing"

        # NFR04: dependencies are pinned for reproducible offline installs
        assert "fastapi==" in pyproject and "sqlalchemy==" in pyproject

    def test_offline_migration(self, tmp_path):
        """Migrations run against a fresh, empty offline database."""
        db_file = tmp_path / "ac09_fresh.db"
        command.upgrade(_alembic_config(f"sqlite+aiosqlite:///{db_file}"), "head")

        tables = _table_names(db_file)
        expected = {
            "branches", "users", "bibliographic_records", "members",
            "items", "inventory_sessions", "audit_logs", "loans",
            "rfid_tags", "gate_events", "notifications", "renewals",
            "fines", "inventory_scans",
        }
        missing = expected - tables
        assert not missing, f"migration did not create: {missing}"

        # The fresh database passes an integrity check
        with sqlite3.connect(db_file) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    def test_update_process(self, tmp_path):
        """An update cycle (current → roll forward) leaves the schema current."""
        db_file = tmp_path / "ac09_update.db"
        cfg = _alembic_config(f"sqlite+aiosqlite:///{db_file}")

        command.upgrade(cfg, "head")
        before = _table_names(db_file)

        # Update = roll forward again; must be idempotent at head
        command.upgrade(cfg, "head")
        assert _table_names(db_file) == before

        with sqlite3.connect(db_file) as conn:
            version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        assert version  # stamped with a concrete revision

    def test_rollback_process(self, tmp_path):
        """Rollback tears the schema down cleanly and can re-apply."""
        db_file = tmp_path / "ac09_rollback.db"
        cfg = _alembic_config(f"sqlite+aiosqlite:///{db_file}")

        command.upgrade(cfg, "head")
        assert len(_table_names(db_file)) > 0

        command.downgrade(cfg, "base")
        assert len(_table_names(db_file)) == 0, "rollback left tables behind"

        # Re-apply after rollback (a failed update can be retried)
        command.upgrade(cfg, "head")
        assert len(_table_names(db_file)) > 0
