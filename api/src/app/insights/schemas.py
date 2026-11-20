"""Pydantic schemas for on-demand query insights (US-12)."""

from pydantic import BaseModel, Field


class InsightsPayload(BaseModel):
    """Structured insights grounded in query results."""

    summary: str
    key_findings: list[str] = Field(default_factory=list)
    next_questions: list[str] = Field(default_factory=list)
