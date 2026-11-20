"""Evaluation service: start golden-set runs and execute them with saved progress."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from app.core.errors import NotFound
from app.evaluation.golden_sets import GOLDEN_SETS
from app.evaluation.metrics import RunHeader, build_run_detail
from app.evaluation.repository import EvalRepository
from app.evaluation.schemas import (
    EvalQuestionResult,
    EvalRunDetail,
    GoldenQuestion,
    GoldenSet,
    GoldenSetSummary,
    QuestionEvalExecution,
)


class EvalRunner(Protocol):
    """Port for executing a single golden question."""

    async def execute_question(self, question_id: str) -> QuestionEvalExecution: ...


RunnerFactory = Callable[[GoldenSet], EvalRunner]


def _result(q: GoldenQuestion, res: QuestionEvalExecution) -> EvalQuestionResult:
    return EvalQuestionResult(
        question_id=q.id,
        question=q.question,
        category=q.category,
        difficulty=q.difficulty,
        outcome=res.outcome,
        generated_sql=res.generated_sql,
        latency_ms=res.latency_ms,
        tokens_in=res.tokens_in,
        tokens_out=res.tokens_out,
        failure_category=res.failure_category,
        plan_skipped=res.plan_skipped,
    )


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

    async def start_run(self, set_name: str) -> EvalRunDetail:
        """Persist a 'running' run for set_name; execute it later with execute_run."""
        golden_set = _golden_set(set_name)
        header = RunHeader(
            id=uuid4(),
            set_name=set_name,
            model=self._model_name,
            prompt_version=self._prompt_version,
            started_at=datetime.now(UTC),
            total_questions=len(golden_set.questions),
        )
        run = build_run_detail(header, [], status="running", finished_at=None)
        return await self._repo.save_run(run)

    async def execute_run(self, run: EvalRunDetail) -> EvalRunDetail:
        """Answer every question, saving progress after each; never raises."""
        header = RunHeader(
            run.id, run.set_name, run.model, run.prompt_version, run.started_at,
            run.total_questions,
        )  # fmt: skip
        results: list[EvalQuestionResult] = []
        try:
            golden_set = _golden_set(run.set_name)
            runner = self.build_runner(golden_set)
            for q in golden_set.questions:
                results.append(_result(q, await runner.execute_question(q.id)))
                await self._repo.save_run(
                    build_run_detail(header, results, status="running", finished_at=None)
                )
        except Exception as exc:  # recorded on the run; details stay out of the response
            failed = build_run_detail(
                header, results, status="failed", finished_at=datetime.now(UTC),
                error=f"Evaluation failed ({type(exc).__name__}).",
            )  # fmt: skip
            return await self._repo.save_run(failed)
        done = build_run_detail(header, results, status="completed", finished_at=datetime.now(UTC))
        return await self._repo.save_run(done)

    async def run_evaluation(self, set_name: str) -> EvalRunDetail:
        """Start and execute a run in one call (used by tests and scripts)."""
        return await self.execute_run(await self.start_run(set_name))

    async def get_run(self, run_id: UUID) -> EvalRunDetail:
        """Fetch a run (running, completed, or failed)."""
        run = await self._repo.get_run(run_id)
        if run is None:
            raise NotFound("Evaluation run not found.")
        return run


def _golden_set(set_name: str) -> GoldenSet:
    golden_set = GOLDEN_SETS.get(set_name)
    if golden_set is None:
        raise NotFound(f"Evaluation set '{set_name}' not found.")
    return golden_set
