"""Evaluation runs execute in the background and report progress (avoids request timeouts)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.errors import NotFound
from app.evaluation.dependencies import get_eval_job, get_eval_service
from app.evaluation.golden_sets import GOLDEN_SETS
from app.evaluation.repository import InMemoryEvalRepository
from app.evaluation.schemas import EvalOutcome, EvalRunDetail, GoldenSet, QuestionEvalExecution
from app.evaluation.service import EvalRunner, EvaluationService
from app.main import create_app

TOTAL = len(GOLDEN_SETS["retail_sales"].questions)


class ProgressCheckingRunner:
    """Records how many results were stored before each question, then answers correctly."""

    def __init__(self, repo: InMemoryEvalRepository) -> None:
        self.repo = repo
        self.seen: list[int] = []

    async def execute_question(self, question_id: str) -> QuestionEvalExecution:
        stored = next(iter(self.repo._runs.values()))
        assert stored.status == "running"
        self.seen.append(len(stored.results))
        return QuestionEvalExecution(outcome=EvalOutcome.CORRECT, latency_ms=1)


class ExplodingRunner:
    async def execute_question(self, question_id: str) -> QuestionEvalExecution:
        raise RuntimeError("secret connection string leaked?")


def _service(runner: EvalRunner, repo: InMemoryEvalRepository) -> EvaluationService:
    def build(_: GoldenSet) -> EvalRunner:
        return runner

    return EvaluationService(repo=repo, runner_factory=build, model_name="fake:model")


async def test_start_run_persists_a_running_run_without_executing_questions() -> None:
    repo = InMemoryEvalRepository()
    service = _service(ExplodingRunner(), repo)

    run = await service.start_run("retail_sales")

    assert run.status == "running"
    assert run.total_questions == TOTAL
    assert run.results == []
    assert run.finished_at is None
    assert (await service.get_run(run.id)).status == "running"


async def test_execute_run_saves_progress_and_completes() -> None:
    repo = InMemoryEvalRepository()
    runner = ProgressCheckingRunner(repo)
    service = _service(runner, repo)
    run = await service.start_run("retail_sales")

    await service.execute_run(run)

    final = await service.get_run(run.id)
    assert final.status == "completed"
    assert final.finished_at is not None
    assert len(final.results) == TOTAL
    assert final.accuracy == 1.0
    assert runner.seen == list(range(TOTAL))


async def test_unexpected_failure_marks_run_failed_without_leaking_details() -> None:
    repo = InMemoryEvalRepository()
    service = _service(ExplodingRunner(), repo)
    run = await service.start_run("retail_sales")

    await service.execute_run(run)

    final = await service.get_run(run.id)
    assert final.status == "failed"
    assert final.error == "Evaluation failed (RuntimeError)."


async def test_start_run_unknown_set_raises_not_found() -> None:
    service = _service(ExplodingRunner(), InMemoryEvalRepository())

    with pytest.raises(NotFound):
        await service.start_run("nope")


async def test_post_returns_202_running_and_the_run_completes_in_the_background() -> None:
    repo = InMemoryEvalRepository()
    service = _service(ProgressCheckingRunner(repo), repo)
    app = create_app()
    app.dependency_overrides[get_eval_service] = lambda: service

    async def job(run: EvalRunDetail) -> None:
        await service.execute_run(run)

    app.dependency_overrides[get_eval_job] = lambda: job

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        started = await client.post("/api/v1/eval/runs", json={"set_name": "retail_sales"})
        assert started.status_code == 202
        assert started.json()["status"] == "running"

        polled = await client.get(f"/api/v1/eval/runs/{started.json()['id']}")

    assert polled.json()["status"] == "completed"
    assert len(polled.json()["results"]) == TOTAL
