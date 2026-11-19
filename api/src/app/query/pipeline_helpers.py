"""Prompt construction and run-record builders for QueryService."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from app.query.executor import ExecutionResult
from app.query.repository import DatasetQueryContext, QueryRunCreate
from app.query.schemas import QueryPlan, QueryRequest, QueryResponse


@dataclass(frozen=True)
class RunMeta:
    """Common metadata for a single query run."""

    run_id: uuid.UUID
    session_id: uuid.UUID
    dataset_id: uuid.UUID
    question: str
    plan: QueryPlan | None
    timings: dict[str, int]
    created_at: datetime


def build_user_prompt(
    ctx: DatasetQueryContext,
    request: QueryRequest,
    recent: list[tuple[str, dict[str, object] | None]],
    *,
    plan: QueryPlan | None,
) -> str:
    """Build the structured user prompt from schema, recent history, and optional plan."""
    parts = [f"Schema:\n{ctx.schema_summary}"]
    if recent:
        history = "\n".join(f"- Q: {q}" for q, _ in recent)
        parts.append(f"Recent questions:\n{history}")
    parts.append(f"Question: {request.question}")
    if request.clarification_choice:
        parts.append(f"User clarification: {request.clarification_choice}")
    if plan is not None:
        parts.append(f"Plan:\n{json.dumps(plan.model_dump())}")
    return "\n\n".join(parts)


def make_run_and_response(
    meta: RunMeta,
    *,
    status: str,
    validation_status: str,
    generated_sql: str | None = None,
    error_code: str | None = None,
    rejection_reasons: list[dict[str, str]] | None = None,
    exec_result: ExecutionResult | None = None,
) -> tuple[QueryRunCreate, QueryResponse]:
    """Build both the persistence payload and public QueryResponse."""
    row_count = exec_result.row_count if exec_result else 0
    truncated = exec_result.truncated if exec_result else False
    run = QueryRunCreate(
        id=meta.run_id,
        session_id=meta.session_id,
        dataset_id=meta.dataset_id,
        question=meta.question,
        plan=meta.plan.model_dump() if meta.plan else None,
        generated_sql=generated_sql,
        validation_status=validation_status,
        rejection_reasons=rejection_reasons,
        status=status,
        error_code=error_code,
        row_count=row_count,
        truncated=truncated,
        stage_timings_ms=meta.timings,
        created_at=meta.created_at,
    )
    return run, _build_response(meta, run, exec_result)


def _build_response(
    meta: RunMeta, run: QueryRunCreate, exec_result: ExecutionResult | None
) -> QueryResponse:
    return QueryResponse(
        id=run.id,
        dataset_id=run.dataset_id,
        question=run.question,
        status=run.status,
        plan=meta.plan,
        generated_sql=run.generated_sql,
        columns=exec_result.columns if exec_result else [],
        rows=exec_result.rows if exec_result else [],
        row_count=run.row_count,
        truncated=run.truncated,
        rejection_reasons=run.rejection_reasons or [],
        stage_timings_ms=run.stage_timings_ms,
        created_at=run.created_at,
    )
