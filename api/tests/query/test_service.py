"""Unit tests for QueryService with fake LLM, executor, and repository (US-07..US-10)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

import pytest
from pydantic import BaseModel

from app.core.errors import NotFound
from app.query.executor import ExecutionResult
from app.query.repository import DatasetQueryContext, QueryRunCreate
from app.query.schemas import (
    QueryHistoryItem,
    QueryPlan,
    QueryRequest,
    SqlGenerationOutput,
)
from app.query.service import QueryService
from app.sessions.schemas import SessionRecord

T = TypeVar("T", bound=BaseModel)


class FakeLLMClient:
    """Deterministic LLMClient fake for unit tests (no network calls)."""

    def __init__(self, responses: list[BaseModel]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        del system_prompt
        self.prompts.append(user_prompt)
        item = self._responses.pop(0)
        assert isinstance(item, response_model)
        return item


class FakeExecutor:
    """Fake read-only executor that records executed SQL."""

    def __init__(self, result: ExecutionResult) -> None:
        self._result = result
        self.executed: list[tuple[str, str]] = []

    async def execute(self, *, schema_name: str, validated_sql: str) -> ExecutionResult:
        self.executed.append((schema_name, validated_sql))
        return self._result


class FakeQueryRepository:
    """In-memory QueryRepository fake."""

    def __init__(self, owner_id: uuid.UUID, ctx: DatasetQueryContext) -> None:
        self._owner_id = owner_id
        self._ctx = ctx
        self.saved: list[QueryRunCreate] = []

    async def get_dataset_context(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID
    ) -> DatasetQueryContext | None:
        if session_id == self._owner_id and dataset_id == self._ctx.dataset_id:
            return self._ctx
        return None

    async def get_recent_questions(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID, limit: int = 3
    ) -> list[tuple[str, dict[str, Any] | None]]:
        del session_id, dataset_id
        return [(r.question, r.plan) for r in self.saved[-limit:]]

    async def save_run(self, payload: QueryRunCreate) -> None:
        self.saved.append(payload)

    async def list_history(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[QueryHistoryItem], int]:
        del session_id, dataset_id
        items = [
            QueryHistoryItem(
                id=r.id,
                question=r.question,
                status=r.status,
                generated_sql=r.generated_sql,
                row_count=r.row_count,
                created_at=r.created_at,
            )
            for r in self.saved[offset : offset + limit]
        ]
        return items, len(self.saved)


def _session() -> SessionRecord:
    now = datetime.now(UTC)
    return SessionRecord(
        id=uuid.uuid4(),
        token_hash="h",
        created_at=now,
        expires_at=now + timedelta(hours=24),
        status="active",
    )


def _ctx() -> DatasetQueryContext:
    """Two tables, so these tests exercise the planned path (see test_plan_skip.py)."""
    return DatasetQueryContext(
        dataset_id=uuid.uuid4(),
        schema_name="ds_1111222233334444",
        table_names=frozenset({"retail_sales", "regions"}),
        schema_summary=(
            "Table retail_sales (8 rows): region (text), revenue (double precision)\n"
            "Table regions (4 rows): region (text), manager (text)"
        ),
    )


async def test_ask_succeeds_and_passes_followup_context() -> None:
    session = _session()
    ctx = _ctx()
    repo = FakeQueryRepository(session.id, ctx)
    llm = FakeLLMClient(
        [
            QueryPlan(intent="Sum revenue by region", tables=["retail_sales"]),
            SqlGenerationOutput(
                sql="SELECT region, SUM(revenue) FROM retail_sales GROUP BY region"
            ),
            QueryPlan(intent="Filter to North", tables=["retail_sales"]),
            SqlGenerationOutput(
                sql=(
                    "SELECT region, SUM(revenue) FROM retail_sales "
                    "WHERE region = 'North' GROUP BY region"
                )
            ),
        ]
    )
    executor = FakeExecutor(
        ExecutionResult(
            columns=["region", "sum"],
            rows=[{"region": "North", "sum": 520.0}],
            row_count=1,
            truncated=False,
        )
    )
    service = QueryService(repo, llm, executor)

    first = await service.ask(session, ctx.dataset_id, QueryRequest(question="Revenue by region"))
    assert first.status == "succeeded"
    assert first.row_count == 1
    assert len(executor.executed) == 1

    await service.ask(session, ctx.dataset_id, QueryRequest(question="Only North"))
    assert "Revenue by region" in llm.prompts[2]


async def test_ambiguous_question_returns_clarification_without_executing() -> None:
    session = _session()
    ctx = _ctx()
    repo = FakeQueryRepository(session.id, ctx)
    llm = FakeLLMClient(
        [
            QueryPlan(
                intent="Top products",
                needs_clarification=True,
                clarifying_question="Rank by revenue or units sold?",
                clarification_options=["By total revenue", "By total units"],
            )
        ]
    )
    executor = FakeExecutor(ExecutionResult(columns=[], rows=[], row_count=0, truncated=False))
    service = QueryService(repo, llm, executor)

    res = await service.ask(session, ctx.dataset_id, QueryRequest(question="Show top products"))
    assert res.status == "needs_clarification"
    assert res.plan is not None
    assert res.plan.clarification_options == ["By total revenue", "By total units"]
    assert executor.executed == []


async def test_unsafe_llm_sql_is_rejected_and_never_executed() -> None:
    session = _session()
    ctx = _ctx()
    repo = FakeQueryRepository(session.id, ctx)
    llm = FakeLLMClient(
        [
            QueryPlan(intent="Delete data", tables=["retail_sales"]),
            SqlGenerationOutput(sql="DELETE FROM retail_sales"),
        ]
    )
    executor = FakeExecutor(ExecutionResult(columns=[], rows=[], row_count=0, truncated=False))
    service = QueryService(repo, llm, executor)

    res = await service.ask(session, ctx.dataset_id, QueryRequest(question="Delete everything"))
    assert res.status == "rejected"
    assert len(res.rejection_reasons) >= 1
    assert executor.executed == []


async def test_foreign_session_cannot_query_dataset() -> None:
    owner = _session()
    intruder = _session()
    ctx = _ctx()
    service = QueryService(
        FakeQueryRepository(owner.id, ctx),
        FakeLLMClient([]),
        FakeExecutor(ExecutionResult(columns=[], rows=[], row_count=0, truncated=False)),
    )
    with pytest.raises(NotFound):
        await service.ask(intruder, ctx.dataset_id, QueryRequest(question="Show all"))
