"""Pydantic schemas for structured chart specifications (ADR-0008)."""

from typing import Literal

from pydantic import BaseModel

ChartType = Literal["bar", "line", "pie", "scatter"]


class ChartSpec(BaseModel):
    """Typed chart specification validated against query result columns."""

    chart_type: ChartType
    x: str
    y: str
    series: str | None = None
    title: str


class ChartValidationResult(BaseModel):
    """Outcome of validating a chart spec against result columns and rows."""

    is_valid: bool
    spec: ChartSpec | None = None
    fallback_reason: str | None = None
