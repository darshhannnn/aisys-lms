"""Spreadsheet import service.

Handles importing data from Excel/CSV files for data migration (FR10, AC01).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List

from openpyxl import load_workbook
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member, MemberCategory, MemberStatus
from app.models.catalogue import BibliographicRecord, Item
from app.repositories.member import MemberRepository
from app.repositories.catalogue import BibliographicRecordRepository, ItemRepository


class SpreadsheetImportService:
    """Service for importing data from spreadsheet files."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.member_repo = MemberRepository(Member, session)
        self.record_repo = BibliographicRecordRepository(BibliographicRecord, session)
        self.item_repo = ItemRepository(Item, session)

    async def import_members_from_excel(
        self,
        file_path: str,
        source_system: str = "legacy_ilms",
    ) -> Dict[str, Any]:
        """Import members from Excel file (FR10, AC01)."""
        wb = load_workbook(file_path, read_only=True)
        ws = wb.active

        imported = 0
        duplicates = 0
        errors = []

        # Skip header row
        for row in ws.iter_rows(min_row=2):
            try:
                member_number = str(row[0].value) if row[0].value else None
                full_name = str(row[1].value) if row[1].value else None
                email = str(row[2].value) if row[2].value else None
                phone = str(row[3].value) if row[3].value else None
                category_str = str(row[4].value) if row[4].value else "student"

                if not member_number or not full_name:
                    continue

                # Check for duplicate
                existing = await self.member_repo.get_by_member_number(member_number)
                if existing:
                    duplicates += 1
                    continue

                # Map category
                category_map = {
                    "student": MemberCategory.STUDENT,
                    "faculty": MemberCategory.FACULTY,
                    "staff": MemberCategory.STAFF,
                    "external": MemberCategory.EXTERNAL,
                    "honorary": MemberCategory.HONORARY,
                }
                category = category_map.get(category_str.lower(), MemberCategory.STUDENT)

                # Create member
                from app.schemas.member import MemberCreate

                member_data = MemberCreate(
                    member_number=member_number,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    category=category,
                    status=MemberStatus.ACTIVE,
                    source_system=source_system,
                    source_id=f"{source_system}_{member_number}",
                )

                await self.member_repo.create(member_data)
                imported += 1

            except Exception as e:
                errors.append(f"Row error: {str(e)}")

        wb.close()

        return {
            "imported": imported,
            "duplicates": duplicates,
            "errors": errors,
            "total": imported + duplicates + len(errors),
        }

    async def import_catalogue_from_excel(
        self,
        file_path: str,
        source_system: str = "legacy_ilms",
    ) -> Dict[str, Any]:
        """Import bibliographic records from Excel file (FR10, AC01)."""
        wb = load_workbook(file_path, read_only=True)
        ws = wb.active

        imported = 0
        duplicates = 0
        errors = []

        for row in ws.iter_rows(min_row=2):
            try:
                title = str(row[0].value) if row[0].value else None
                author = str(row[1].value) if row[1].value else None
                isbn = str(row[2].value) if row[2].value else None
                publisher = str(row[3].value) if row[3].value else None
                publication_year = int(row[4].value) if row[4].value else None

                if not title or not author:
                    continue

                # Check for duplicate by ISBN
                if isbn:
                    existing = await self.record_repo.get_by_isbn(isbn)
                    if existing:
                        duplicates += 1
                        continue

                # Create record
                from app.schemas.catalogue import BibliographicRecordCreate

                record_data = BibliographicRecordCreate(
                    title=title,
                    author=author,
                    isbn=isbn,
                    publisher=publisher,
                    publication_year=publication_year,
                )

                await self.record_repo.create(record_data)
                imported += 1

            except Exception as e:
                errors.append(f"Row error: {str(e)}")

        wb.close()

        return {
            "imported": imported,
            "duplicates": duplicates,
            "errors": errors,
            "total": imported + duplicates + len(errors),
        }

    async def reconcile_data(
        self,
        source_system: str,
    ) -> Dict[str, Any]:
        """Reconcile imported data with existing records (FR10, AC01)."""
        # Get all records from source system
        from sqlalchemy import select

        result = await self.session.execute(
            select(Member).where(Member.source_system == source_system)
        )
        members = result.scalars().all()
        
        reconciliation_report = {
            "source_system": source_system,
            "total_members": len(members),
            "reconciled": 0,
            "flagged": 0,
        }

        for member in members:
            # Check if member has valid data
            if not member.email and not member.phone:
                reconciliation_report["flagged"] += 1
            else:
                reconciliation_report["reconciled"] += 1

        return reconciliation_report
