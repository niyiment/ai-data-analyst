"""Evaluation against the real demo schema and app.eval_runs (migrations 0004, 0005)."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.evaluation.golden_sets import GOLDEN_SETS
from app.evaluation.repository import SqlEvalRepository
from app.evaluation.schemas import EvalRunDetail, GoldenQuestion
from app.query.executor import PostgresReadOnlyExecutor
from app.query.validator.pipeline import validate_sql
from app.query.validator.types import ValidationContext

RETAIL = GOLDEN_SETS["retail_sales"]
CTX = ValidationContext(allowed_schema=RETAIL.demo_schema, allowed_tables=RETAIL.allowed_tables())


def _executor() -> PostgresReadOnlyExecutor:
    return PostgresReadOnlyExecutor(get_settings().database_url_analyst)


async def _rows(sql: str) -> list[dict[str, object]]:
    normalized = validate_sql(sql, CTX).normalized_sql
    assert normalized is not None
    result = await _executor().execute(schema_name=RETAIL.demo_schema, validated_sql=normalized)
    return result.rows


@pytest.mark.parametrize("question", RETAIL.questions, ids=lambda q: q.id)
async def test_reference_sql_runs_as_analyst_ro_and_returns_rows(question: GoldenQuestion) -> None:
    assert await _rows(question.reference_sql)


@pytest.mark.parametrize(
    ("question_id", "expected"),
    [
        ("rs-01", [{"total_orders": 40}]),
        ("rs-21", [{"region": "West"}]),
        ("rs-28", [{"order_id": 1039, "revenue": "1260.00"}]),
    ],
)
async def test_known_answers(question_id: str, expected: list[dict[str, object]]) -> None:
    question = next(q for q in RETAIL.questions if q.id == question_id)

    assert await _rows(question.reference_sql) == expected


async def test_total_revenue_matches_seed_data() -> None:
    rows = await _rows("SELECT SUM(revenue) AS total FROM retail_sales")

    assert Decimal(str(rows[0]["total"])) == Decimal("9120.00")


async def test_sql_eval_repository_round_trips_a_run() -> None:
    engine = create_async_engine(get_settings().database_url_app)
    now = datetime.now(UTC)
    run = EvalRunDetail(
        id=uuid4(), set_name="retail_sales", prompt_version="v1", model="test:integration",
        started_at=now, finished_at=now, total_questions=0, correct_count=0, rejected_count=0,
        accuracy=0.0, rejection_rate=0.0, p50_latency_ms=0, p95_latency_ms=0,
        total_tokens_in=0, total_tokens_out=0, failure_categories={}, results=[],
    )  # fmt: skip
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            await SqlEvalRepository(db).save_run(run)
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            assert await SqlEvalRepository(db).get_run(run.id) == run
    finally:
        await engine.dispose()
