"""Simple single-table questions skip the plan stage (PRD FR-05, ADR-0006)."""

import uuid

import pytest

from app.query.executor import ExecutionResult
from app.query.pipeline_helpers import should_skip_plan
from app.query.repository import DatasetQueryContext
from app.query.schemas import QueryRequest, SqlGenerationOutput
from app.query.service import QueryService
from tests.query.test_service import FakeExecutor, FakeLLMClient, FakeQueryRepository, _session

ONE = frozenset({"retail_sales"})
TWO = frozenset({"retail_sales", "regions"})


@pytest.mark.parametrize(
    ("tables", "question", "skip"),
    [
        (ONE, "What is the total revenue by region?", True),
        (ONE, "List the top 3 products by units", True),
        (ONE, "How many orders were returned?", True),
        (TWO, "What is the total revenue by region?", False),
        (ONE, "What are our best products?", False),
        (ONE, "Show me the recent sales", False),
        (ONE, "Which region is performing well?", False),
        (ONE, "Show top products", False),
    ],
)
def test_should_skip_plan(tables: frozenset[str], question: str, skip: bool) -> None:
    assert should_skip_plan(tables, question) is skip


async def test_simple_single_table_question_goes_straight_to_sql() -> None:
    session = _session()
    ctx = DatasetQueryContext(
        dataset_id=uuid.uuid4(),
        schema_name="ds_1111222233334444",
        table_names=ONE,
        schema_summary="Table retail_sales (8 rows): region (text), revenue (double precision)",
    )
    llm = FakeLLMClient(
        [SqlGenerationOutput(sql="SELECT region, SUM(revenue) FROM retail_sales GROUP BY region")]
    )
    executor = FakeExecutor(
        ExecutionResult(columns=["region"], rows=[{"region": "North"}], row_count=1, truncated=False)
    )
    service = QueryService(FakeQueryRepository(session.id, ctx), llm, executor)

    res = await service.ask(session, ctx.dataset_id, QueryRequest(question="Revenue by region"))

    assert res.status == "succeeded"
    assert res.plan is None
    assert len(llm.prompts) == 1
    assert "plan" not in res.stage_timings_ms
