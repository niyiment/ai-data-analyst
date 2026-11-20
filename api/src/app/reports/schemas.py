"""Pydantic schemas for pinned reports and export (US-13)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReportItemInput(BaseModel):
    """A single query run pinned to a new report."""

    query_run_id: uuid.UUID
    note: str | None = None


class CreateReportRequest(BaseModel):
    """HTTP request body for creating a report."""

    title: str = Field(min_length=1, max_length=200)
    items: list[ReportItemInput] = Field(min_length=1, max_length=50)


class ReportItemView(BaseModel):
    """Hydrated report item with question, SQL, and optional note."""

    id: uuid.UUID
    query_run_id: uuid.UUID
    position: int
    question: str
    generated_sql: str | None = None
    note: str | None = None


class ReportResponse(BaseModel):
    """Public report representation."""

    id: uuid.UUID
    title: str
    created_at: datetime
    items: list[ReportItemView] = Field(default_factory=list)
