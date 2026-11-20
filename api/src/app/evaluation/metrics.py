"""Aggregate per-question results into run-level evaluation metrics (docs/TESTING.md 9.2)."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from math import ceil
from uuid import UUID

from app.evaluation.schemas import EvalOutcome, EvalQuestionResult, EvalRunDetail, RunStatus


@dataclass(frozen=True)
class RunHeader:
    """Identity of a run that does not change while it executes."""

    id: UUID
    set_name: str
    model: str
    prompt_version: str
    started_at: datetime
    total_questions: int


def percentile(values: list[int], pct: float) -> int:
    """Nearest-rank percentile; 0 for no values."""
    if not values:
        return 0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, ceil(pct * len(ordered)) - 1))
    return ordered[idx]


def accuracy_by_path(results: list[EvalQuestionResult]) -> dict[str, float]:
    """Accuracy for 'direct' (plan skipped) and 'planned' questions, for paths that ran."""
    by_path: dict[str, list[EvalQuestionResult]] = {}
    for r in results:
        by_path.setdefault("direct" if r.plan_skipped else "planned", []).append(r)
    return {
        path: sum(r.outcome == EvalOutcome.CORRECT for r in items) / len(items)
        for path, items in by_path.items()
    }


def build_run_detail(
    header: RunHeader,
    results: list[EvalQuestionResult],
    *,
    status: RunStatus,
    finished_at: datetime | None,
    error: str | None = None,
) -> EvalRunDetail:
    """Summarise the results answered so far; rates use the number answered."""
    answered = len(results)
    correct = sum(1 for r in results if r.outcome == EvalOutcome.CORRECT)
    rejected = sum(1 for r in results if r.outcome == EvalOutcome.REJECTED)
    latencies = [r.latency_ms for r in results]
    return EvalRunDetail(
        id=header.id,
        set_name=header.set_name,
        prompt_version=header.prompt_version,
        model=header.model,
        started_at=header.started_at,
        finished_at=finished_at,
        status=status,
        error=error,
        total_questions=header.total_questions,
        correct_count=correct,
        rejected_count=rejected,
        accuracy=correct / answered if answered else 0.0,
        rejection_rate=rejected / answered if answered else 0.0,
        p50_latency_ms=percentile(latencies, 0.50),
        p95_latency_ms=percentile(latencies, 0.95),
        total_tokens_in=sum(r.tokens_in for r in results),
        total_tokens_out=sum(r.tokens_out for r in results),
        failure_categories=dict(Counter(r.failure_category for r in results if r.failure_category)),
        accuracy_by_path=accuracy_by_path(results),
        results=results,
    )
