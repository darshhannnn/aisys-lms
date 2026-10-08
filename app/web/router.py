"""Jinja2 web router — serves the staff UI and OPAC pages."""
from __future__ import annotations

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.reporting import ReportingService

router = APIRouter()

# Alias used by app.main
web_router = router
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Dashboard page with statistics (FR08, AC08)."""
    reporting_service = ReportingService(db)
    stats = await reporting_service.get_dashboard_stats()
    return templates.TemplateResponse("dashboard.html", {"request": request, "stats": stats})


@router.get("/catalogue", response_class=HTMLResponse, include_in_schema=False)
async def catalogue_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("catalogue/list.html", {"request": request})


@router.get("/circulation", response_class=HTMLResponse, include_in_schema=False)
async def circulation_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("circulation/checkout.html", {"request": request})


@router.get("/members", response_class=HTMLResponse, include_in_schema=False)
async def members_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("members/list.html", {"request": request})


@router.get("/rfid", response_class=HTMLResponse, include_in_schema=False)
async def rfid_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("rfid/tagging.html", {"request": request})


@router.get("/reports", response_class=HTMLResponse, include_in_schema=False)
async def reports_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("reports/dashboard.html", {"request": request})
