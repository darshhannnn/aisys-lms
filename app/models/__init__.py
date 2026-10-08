"""Import all ORM models so SQLAlchemy registers every mapper.

Alembic and the test suite rely on importing this package to populate
``Base.metadata`` with the full schema.
"""
from app.models.audit import AuditLog
from app.models.catalogue import BibliographicRecord, Item
from app.models.circulation import Fine, Loan, Renewal
from app.models.member import Member
from app.models.notification import Notification
from app.models.rfid import GateEvent, InventoryScan, InventorySession, RfidTag

__all__ = [
    "AuditLog",
    "BibliographicRecord",
    "Fine",
    "GateEvent",
    "InventoryScan",
    "InventorySession",
    "Item",
    "Loan",
    "Member",
    "Notification",
    "Renewal",
    "RfidTag",
    "User",
]
