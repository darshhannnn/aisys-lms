"""API v1 router aggregator."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    catalogue,
    circulation,
    health,
    members,
    migration,
    rfid,
    reports,
    inventory,
    gate_events,
    notifications,
)

api_router = APIRouter()

api_router.include_router(health.router,       prefix="/health",        tags=["Health"])
api_router.include_router(auth.router,         prefix="/auth",          tags=["Auth"])
api_router.include_router(catalogue.router,    prefix="/catalogue",     tags=["Catalogue"])
api_router.include_router(members.router,      prefix="/members",       tags=["Members"])
api_router.include_router(circulation.router,  prefix="/circulation",   tags=["Circulation"])
api_router.include_router(rfid.router,         prefix="/rfid",          tags=["RFID"])
api_router.include_router(inventory.router,    prefix="/inventory",     tags=["Inventory"])
api_router.include_router(gate_events.router,  prefix="/gate-events",   tags=["Gate Events"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(reports.router,      prefix="/reports",       tags=["Reports"])
api_router.include_router(migration.router,    prefix="/migration",     tags=["Migration"])
