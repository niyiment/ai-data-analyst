"""Pydantic schemas for the two-stage NL-to-SQL query pipeline (ADR-0006)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.charts.schemas import ChartSpec


class QueryPlan(BaseModel):
    """Structured output of Stage 1 (plan)."""

    intent: str
    tables: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    aggregations: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarifying_question: str | None = None
    clarification_options: list[str] = Field(default_factory=list)


class SqlGenerationOutput(BaseModel):
    """Structured output of Stage 2 (SQL generation)."""

    sql: str
    explanation: str = ""


class QueryRequest(BaseModel):
    """HTTP request body for asking a natural-language question."""

    question: str = Field(min_length=2, max_length=1000)
    clarification_choice: str | None = None


class QueryResponse(BaseModel):
    """HTTP response returned for a query run (US-07, US-08, US-09)."""

    id: uuid.UUID
    dataset_id: uuid.UUID
    question: str
    status: str
    plan: QueryPlan | None = None
    generated_sql: str | None = None
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    rejection_reasons: list[dict[str, str]] = Field(default_factory=list)
    stage_timings_ms: dict[str, int] = Field(default_factory=dict)
    chart_spec: ChartSpec | None = None
    created_at: datetime


class QueryHistoryItem(BaseModel):
    """Compact query history record."""

    id: uuid.UUID
    question: str
    status: str
    generated_sql: str | None = None
    row_count: int
    created_at: datetime


class QueryHistoryResponse(BaseModel):
    """Paginated query history for a dataset."""

    items: list[QueryHistoryItem]
    total: int
