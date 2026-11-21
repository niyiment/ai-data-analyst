"""TDD tests for ReportService and safe HTML/PDF export (US-13, SECURITY.md)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.errors import NotFound
from app.reports.exporter import neutralize_formula, render_report_html, render_report_pdf
from app.reports.schemas import (
    CreateReportRequest,
    ReportItemInput,
    ReportItemView,
    ReportResponse,
)
from app.reports.service import ReportService
from app.sessions.schemas import SessionRecord


class FakeReportRepository:
    def __init__(self, owner_id: uuid.UUID) -> None:
        self._owner_id = owner_id
        self.reports: dict[uuid.UUID, ReportResponse] = {}

    async def create_report(
        self,
        *,
        session_id: uuid.UUID,
        title: str,
        items: list[ReportItemInput],
        created_at: datetime,
    ) -> ReportResponse:
        report_id = uuid.uuid4()
        views = [
            ReportItemView(
                id=uuid.uuid4(),
                query_run_id=item.query_run_id,
                position=idx,
                question=f"Question {idx + 1}",
                generated_sql="SELECT 1",
                note=item.note,
            )
            for idx, item in enumerate(items)
        ]
        report = ReportResponse(
            id=report_id,
            title=title,
            created_at=created_at,
            items=views,
        )
        if session_id == self._owner_id:
            self.reports[report_id] = report
        return report

    async def get_report(
        self, session_id: uuid.UUID, report_id: uuid.UUID
    ) -> ReportResponse | None:
        if session_id != self._owner_id:
            return None
        return self.reports.get(report_id)


def _session() -> SessionRecord:
    now = datetime.now(UTC)
    return SessionRecord(
        id=uuid.uuid4(),
        token_hash="h",
        created_at=now,
        expires_at=now + timedelta(hours=24),
        status="active",
    )


def test_neutralize_formula_prefixes_dangerous_leaders() -> None:
    assert neutralize_formula("=CMD()") == "'=CMD()"
    assert neutralize_formula("+1+1") == "'+1+1"
    assert neutralize_formula("-1") == "'-1"
    assert neutralize_formula("@SUM(A1)") == "'@SUM(A1)"
    assert neutralize_formula("North") == "North"


def test_render_report_html_escapes_xss() -> None:
    report = ReportResponse(
        id=uuid.uuid4(),
        title="<script>alert(1)</script> Sales",
        created_at=datetime.now(UTC),
        items=[
            ReportItemView(
                id=uuid.uuid4(),
                query_run_id=uuid.uuid4(),
                position=0,
                question="=HYPERLINK('evil')",
                generated_sql="SELECT * FROM retail_sales",
                note="<b>Important</b>",
            )
        ],
    )
    html_doc = render_report_html(report)
    assert "<script>" not in html_doc
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_doc
    assert "&#x27;=HYPERLINK" in html_doc


def test_render_report_pdf_returns_valid_pdf_bytes() -> None:
    report = ReportResponse(
        id=uuid.uuid4(),
        title="Q1 Summary",
        created_at=datetime.now(UTC),
        items=[],
    )
    pdf_bytes = render_report_pdf(report)
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf_bytes


async def test_report_service_create_export_and_ownership() -> None:
    owner = _session()
    intruder = _session()
    service = ReportService(FakeReportRepository(owner.id))

    created = await service.create_report(
        owner,
        CreateReportRequest(
            title="Executive Summary",
            items=[ReportItemInput(query_run_id=uuid.uuid4(), note="Key metric")],
        ),
    )
    assert created.title == "Executive Summary"
    assert len(created.items) == 1

    content_type, body = await service.export_report(owner, created.id, fmt="html")
    assert content_type == "text/html; charset=utf-8"
    assert b"Executive Summary" in body

    with pytest.raises(NotFound):
        await service.export_report(intruder, created.id, fmt="html")
