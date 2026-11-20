"""HTTP router for reports creation and HTML/PDF export (US-13)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.reports.dependencies import get_report_service
from app.reports.schemas import CreateReportRequest, ReportResponse
from app.reports.service import ReportService
from app.sessions.dependencies import require_session
from app.sessions.schemas import SessionRecord

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("", response_model=ReportResponse, status_code=201)
async def create_report(
    payload: CreateReportRequest,
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[ReportService, Depends(get_report_service)],
) -> ReportResponse:
    """Create a report from pinned query runs."""
    return await service.create_report(session, payload)


@router.get("/{report_id}/export")
async def export_report(
    report_id: uuid.UUID,
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[ReportService, Depends(get_report_service)],
    fmt: Annotated[str, Query(alias="format")] = "html",
) -> Response:
    """Download a report as HTML or PDF."""
    media_type, content = await service.export_report(session, report_id, fmt=fmt)
    ext = "pdf" if fmt.lower() == "pdf" else "html"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.{ext}"'},
    )
