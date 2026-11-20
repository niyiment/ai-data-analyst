"""Evaluation service orchestrating golden-set runs and metric aggregation."""

from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from math import ceil
from typing import Protocol
from uuid import UUID, uuid4

from app.core.errors import NotFound
from app.evaluation.golden_sets import GOLDEN_SETS
from app.evaluation.repository import EvalRepository
from app.evaluation.schemas import (
    EvalOutcome,
    EvalQuestionResult,
    EvalRunDetail,
    GoldenSet,
    GoldenSetSummary,
    QuestionEvalExecution,
)


class EvalRunner(Protocol):
    """Port for executing a single golden question."""

    async def execute_question(self, question_id: str) -> QuestionEvalExecution: ...


RunnerFactory = Callable[[GoldenSet], EvalRunner]


def _percentile(values: list[int], pct: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, ceil(pct * len(ordered)) - 1))
    return ordered[idx]


class EvaluationService:
    """Runs golden question sets and computes accuracy, latency, and token metrics."""

    def __init__(
        self,
        repo: EvalRepository,
        runner_factory: RunnerFactory,
        model_name: str = "unknown",
        prompt_version: str = "v1",
    ) -> None:
        self._repo = repo
        self._runner_factory = runner_factory
        self._model_name = model_name
        self._prompt_version = prompt_version

    @property
    def repository(self) -> EvalRepository:
        """The run store this service writes to."""
        return self._repo

    @property
    def model_name(self) -> str:
        """Label of the model under evaluation, e.g. 'gemini:gemini-2.5-flash'."""
        return self._model_name

    def build_runner(self, golden_set: GoldenSet) -> EvalRunner:
        """Create the runner that answers one golden set."""
        return self._runner_factory(golden_set)

    def list_sets(self) -> list[GoldenSetSummary]:
        """Return summaries of all registered golden sets."""
        return [
            GoldenSetSummary(
                name=s.name,
                demo_schema=s.demo_schema,
                description=s.description,
                question_count=len(s.questions),
            )
            for s in GOLDEN_SETS.values()
        ]

    async def run_evaluation(self, set_name: str) -> EvalRunDetail:
        """Execute all questions in a golden set and persist the aggregated run."""
        golden_set = GOLDEN_SETS.get(set_name)
        if golden_set is None:
            raise NotFound(f"Evaluation set '{set_name}' not found.")

        runner = self.build_runner(golden_set)
        started_at = datetime.now(UTC)
        results: list[EvalQuestionResult] = []
        for q in golden_set.questions:
            exec_res = await runner.execute_question(q.id)
            results.append(
                EvalQuestionResult(
                    question_id=q.id,
                    question=q.question,
                    category=q.category,
                    difficulty=q.difficulty,
                    outcome=exec_res.outcome,
                    generated_sql=exec_res.generated_sql,
                    latency_ms=exec_res.latency_ms,
                    tokens_in=exec_res.tokens_in,
                    tokens_out=exec_res.tokens_out,
                    failure_category=exec_res.failure_category,
                )
            )
        return await self._repo.save_run(self._build_detail(set_name, started_at, results))

    async def get_run(self, run_id: UUID) -> EvalRunDetail:
        """Fetch a previously completed evaluation run."""
        run = await self._repo.get_run(run_id)
        if run is None:
            raise NotFound("Evaluation run not found.")
        return run

    def _build_detail(
        self,
        set_name: str,
        started_at: datetime,
        results: list[EvalQuestionResult],
    ) -> EvalRunDetail:
        total = len(results)
        correct = sum(1 for r in results if r.outcome == EvalOutcome.CORRECT)
        rejected = sum(1 for r in results if r.outcome == EvalOutcome.REJECTED)
        latencies = [r.latency_ms for r in results]
        failures = Counter(r.failure_category for r in results if r.failure_category)

        return EvalRunDetail(
            id=uuid4(),
            set_name=set_name,
            prompt_version=self._prompt_version,
            model=self._model_name,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            total_questions=total,
            correct_count=correct,
            rejected_count=rejected,
            accuracy=correct / total if total else 0.0,
            rejection_rate=rejected / total if total else 0.0,
            p50_latency_ms=_percentile(latencies, 0.50),
            p95_latency_ms=_percentile(latencies, 0.95),
            total_tokens_in=sum(r.tokens_in for r in results),
            total_tokens_out=sum(r.tokens_out for r in results),
            failure_categories=dict(failures),
            results=results,
        )
