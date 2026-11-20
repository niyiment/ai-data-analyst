"""Unit tests for evaluation run repositories (US-14)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.evaluation.repository import InMemoryEvalRepository, model_to_run, run_to_model
from app.evaluation.schemas import EvalOutcome, EvalQuestionResult, EvalRunDetail


def _run() -> EvalRunDetail:
    now = datetime.now(UTC)
    return EvalRunDetail(
        id=uuid4(),
        set_name="retail_sales",
        prompt_version="v1",
        model="ollama:llama3.2",
        started_at=now,
        finished_at=now,
        total_questions=1,
        correct_count=0,
        rejected_count=1,
        accuracy=0.0,
        rejection_rate=1.0,
        p50_latency_ms=12,
        p95_latency_ms=12,
        total_tokens_in=0,
        total_tokens_out=0,
        failure_categories={"validator_rejected": 1},
        results=[
            EvalQuestionResult(
                question_id="rs-01",
                question="How many orders?",
                category="aggregate",
                difficulty="easy",
                outcome=EvalOutcome.REJECTED,
                generated_sql="DELETE FROM retail_sales",
                latency_ms=12,
                tokens_in=0,
                tokens_out=0,
                failure_category="validator_rejected",
            )
        ],
    )


@pytest.mark.asyncio
async def test_in_memory_repository_round_trips_runs() -> None:
    repo = InMemoryEvalRepository()
    run = _run()

    await repo.save_run(run)

    assert await repo.get_run(run.id) == run
    assert await repo.get_run(uuid4()) is None


def test_sql_model_mapping_round_trips_every_field() -> None:
    run = _run()

    model = run_to_model(run)

    assert model.id == run.id
    assert model.set_name == "retail_sales"
    assert model.accuracy == 0.0
    assert model_to_run(model) == run
