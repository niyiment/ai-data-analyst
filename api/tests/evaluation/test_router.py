"""API tests for /api/v1/eval endpoints (US-14 & US-15)."""

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.evaluation.dependencies import get_eval_job, get_eval_service
from app.evaluation.repository import InMemoryEvalRepository
from app.evaluation.schemas import EvalOutcome, EvalRunDetail, QuestionEvalExecution
from app.evaluation.service import EvaluationService
from app.main import create_app


class AlwaysCorrectRunner:
    """Fake runner so router tests never touch an LLM or database."""

    async def execute_question(self, question_id: str) -> QuestionEvalExecution:
        return QuestionEvalExecution(outcome=EvalOutcome.CORRECT, latency_ms=5)


@pytest.fixture
def app() -> Iterator[FastAPI]:
    application = create_app()
    service = EvaluationService(
        repo=InMemoryEvalRepository(),
        runner_factory=lambda _set: AlwaysCorrectRunner(),
        model_name="fake:model",
    )
    application.dependency_overrides[get_eval_service] = lambda: service

    async def job(run: EvalRunDetail) -> None:
        await service.execute_run(run)

    application.dependency_overrides[get_eval_job] = lambda: job
    yield application


@pytest.mark.asyncio
async def test_eval_sets_and_run_lifecycle(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sets_resp = await client.get("/api/v1/eval/sets")
        assert sets_resp.status_code == 200
        assert any(s["name"] == "retail_sales" for s in sets_resp.json())

        run_resp = await client.post("/api/v1/eval/runs", json={"set_name": "retail_sales"})
        assert run_resp.status_code == 202
        run = run_resp.json()
        assert run["set_name"] == "retail_sales"
        assert run["model"] == "fake:model"

        get_resp = await client.get(f"/api/v1/eval/runs/{run['id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "completed"
        assert get_resp.json()["accuracy"] == 1.0


@pytest.mark.asyncio
async def test_eval_run_not_found_returns_standard_error(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/v1/eval/runs/{uuid4()}")
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == "NOT_FOUND"
        assert "request_id" in body
