"""Pydantic schemas for evaluation sets, runs, and results (docs/TESTING.md)."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class EvalOutcome(StrEnum):
    """Possible outcomes for a single golden question evaluation."""

    CORRECT = "correct"
    WRONG = "wrong"
    REJECTED = "rejected"
    ERROR = "error"


class GoldenQuestion(BaseModel):
    """Single golden question with reference SQL."""

    id: str
    question: str
    reference_sql: str
    category: str
    difficulty: str
    order_sensitive: bool = False
    expects_clarification: bool = False


class GoldenSet(BaseModel):
    """Named collection of golden questions for a demo schema."""

    name: str
    demo_schema: str
    description: str
    schema_summary: str = ""
    table_names: list[str] = Field(default_factory=list)
    questions: list[GoldenQuestion]

    def allowed_tables(self) -> frozenset[str]:
        """Tables the validator may reference; defaults to a table named after the set."""
        return frozenset(self.table_names or [self.name])


class GoldenSetSummary(BaseModel):
    """Summary metadata for a golden set."""

    name: str
    demo_schema: str
    description: str
    question_count: int


class QuestionEvalExecution(BaseModel):
    """Raw execution outcome returned by an evaluation runner."""

    outcome: EvalOutcome
    generated_sql: str | None = None
    latency_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    failure_category: str | None = None
    plan_skipped: bool = False


class EvalQuestionResult(BaseModel):
    """Recorded result for one golden question in an eval run."""

    question_id: str
    question: str
    category: str
    difficulty: str
    outcome: EvalOutcome
    generated_sql: str | None = None
    latency_ms: int
    tokens_in: int
    tokens_out: int
    failure_category: str | None = None
    plan_skipped: bool = False


class EvalRunCreate(BaseModel):
    """Request body for starting an evaluation run."""

    set_name: str = Field(min_length=1, max_length=64)


class EvalRunDetail(BaseModel):
    """Aggregated metrics and per-question results for an evaluation run."""

    id: UUID
    set_name: str
    prompt_version: str
    model: str
    started_at: datetime
    finished_at: datetime
    total_questions: int
    correct_count: int
    rejected_count: int
    accuracy: float
    rejection_rate: float
    p50_latency_ms: int
    p95_latency_ms: int
    total_tokens_in: int
    total_tokens_out: int
    failure_categories: dict[str, int]
    accuracy_by_path: dict[str, float] = Field(default_factory=dict)
    results: list[EvalQuestionResult]
