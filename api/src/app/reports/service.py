"""Business logic service for building and exporting reports (US-13)."""

import uuid
from datetime import UTC, datetime

from app.core.errors import NotFound, ValidationRejected
from app.reports.exporter import render_report_html, render_report_pdf
from app.reports.repository import ReportRepository
from app.reports.schemas import CreateReportRequest, ReportResponse
from app.sessions.schemas import SessionRecord


class ReportService:
    """Orchestrates report creation and safe HTML/PDF export."""

    def __init__(self, repo: ReportRepository) -> None:
        self._repo = repo

    async def create_report(
        self, session: SessionRecord, payload: CreateReportRequest
    ) -> ReportResponse:
        """Persist a new report with pinned query runs."""
        return await self._repo.create_report(
            session_id=session.id,
            title=payload.title,
            items=payload.items,
            created_at=datetime.now(UTC),
        )

    async def export_report(
        self, session: SessionRecord, report_id: uuid.UUID, *, fmt: str = "html"
    ) -> tuple[str, bytes]:
        """Export an owned report as HTML or PDF."""
        report = await self._repo.get_report(session.id, report_id)
        if report is None:
            raise NotFound("Report not found.")

        normalized = fmt.lower()
        if normalized == "html":
            return "text/html; charset=utf-8", render_report_html(report).encode("utf-8")
        if normalized == "pdf":
            return "application/pdf", render_report_pdf(report)
        raise ValidationRejected("Export format must be 'html' or 'pdf'.")
