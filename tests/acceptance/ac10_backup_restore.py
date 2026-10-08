"""AC10: Restore from backup and data integrity validation.

Acceptance test for backup and restore (FR10, NFR01).
"""
from __future__ import annotations

import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401  — registers all mappers on Base.metadata
from app.core.config import settings
from app.db.base import Base
from app.models.audit import AuditLog
from app.models.catalogue import BibliographicRecord
from cli.migrate import backup, restore


@pytest.mark.acceptance
class TestAC10BackupRestore:
    """Acceptance tests for database backup and restore (AC10)."""

    @pytest.fixture()
    def seeded_db(self, tmp_path, monkeypatch):
        """A live SQLite database with catalogue + audit data, and its backup."""
        db_file = tmp_path / "ac10_live.db"
        db_url = f"sqlite:///{db_file}"

        engine = create_engine(db_url, future=True)
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            session.add_all(
                [
                    BibliographicRecord(
                        title="AC10 Seed Book",
                        author="AC10 Author",
                        isbn=f"AC10-{uuid.uuid4().hex[:10]}",
                    ),
                    AuditLog(
                        action="ac10.backup_test",
                        resource_type="test",
                        actor_username="ac10-tester",
                    ),
                ]
            )
            session.commit()

        engine.dispose()  # release the file lock (Windows) before tests copy/delete it

        # Point the CLI at the seeded database
        monkeypatch.setattr(settings, "database_url_sync", db_url, raising=False)
        backup_path = backup(destination=str(tmp_path / "ac10_backup.db"))

        return db_file, Path(backup_path)

    def test_database_backup(self, seeded_db):
        """Backup produces a verified copy of the live database."""
        db_file, backup_path = seeded_db

        assert backup_path.is_file()
        assert backup_path.stat().st_size > 0

        with sqlite3.connect(backup_path) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            tables = {n for (n,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "bibliographic_records" in tables
        assert "audit_logs" in tables

    def test_database_restore(self, seeded_db):
        """Restore recovers the data after the live database is destroyed."""
        db_file, backup_path = seeded_db

        # Simulate data loss: wipe the live database
        db_file.unlink()
        db_file.touch()

        restore(str(backup_path), force=True)

        with sqlite3.connect(db_file) as conn:
            titles = conn.execute(
                "SELECT title FROM bibliographic_records WHERE title LIKE 'AC10%'"
            ).fetchall()
        assert ("AC10 Seed Book",) in titles

    def test_data_integrity_validation(self, seeded_db):
        """Row counts match between the live database and its backup."""
        db_file, backup_path = seeded_db

        with sqlite3.connect(db_file) as live, sqlite3.connect(backup_path) as bak:
            live_counts = {
                table: live.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("bibliographic_records", "audit_logs")
            }
            bak_counts = {
                table: bak.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("bibliographic_records", "audit_logs")
            }
            assert live.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

        assert live_counts == bak_counts

    def test_audit_log_preservation(self, seeded_db):
        """NFR02: audit entries survive a backup/restore cycle unchanged."""
        db_file, backup_path = seeded_db

        with closing(sqlite3.connect(db_file)) as conn:
            before = conn.execute(
                "SELECT action, resource_type, actor_username FROM audit_logs WHERE action='ac10.backup_test'"
            ).fetchall()

        db_file.unlink()
        db_file.touch()
        restore(str(backup_path), force=True)

        with closing(sqlite3.connect(db_file)) as conn:
            after = conn.execute(
                "SELECT action, resource_type, actor_username FROM audit_logs WHERE action='ac10.backup_test'"
            ).fetchall()

        assert before == after
        assert before == [("ac10.backup_test", "test", "ac10-tester")]
