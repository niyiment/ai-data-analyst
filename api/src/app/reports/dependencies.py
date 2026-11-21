"""FastAPI dependencies for the reports module."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.reports.repository import SqlReportRepository
from app.reports.service import ReportService


def get_report_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReportService:
    """Construct a ReportService backed by PostgreSQL."""
    return ReportService(SqlReportRepository(db))
