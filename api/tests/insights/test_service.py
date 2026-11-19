"""TDD tests for on-demand InsightsService (US-12)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import TypeVar

import pytest
from pydantic import BaseModel

from app.core.errors import NotFound
from app.insights.repository import QueryRunSummary
from app.insights.schemas import InsightsPayload
from app.insights.service import InsightsService
from app.sessions.schemas import SessionRecord

T = TypeVar("T", bound=BaseModel)


class FakeLLM:
    def __init__(self, payload: InsightsPayload) -> None:
        self._payload = payload
        self.calls = 0

    async def generate_structured(
        self, *, system_prompt: str, user_prompt: str, response_model: type[T]
    ) -> T:
        del system_prompt, user_prompt
        self.calls += 1
        assert isinstance(self._payload, response_model)
        return self._payload


class FakeInsightsRepository:
    def __init__(self, owner_id: uuid.UUID, run: QueryRunSummary) -> None:
        self._owner_id = owner_id
        self._run = run
        self._cached: InsightsPayload | None = None

    async def get_query_run(
        self, session_id: uuid.UUID, query_run_id: uuid.UUID
    ) -> QueryRunSummary | None:
        if session_id == self._owner_id and query_run_id == self._run.id:
            return self._run
        return None

    async def get_cached_insights(self, query_run_id: uuid.UUID) -> InsightsPayload | None:
        del query_run_id
        return self._cached

    async def save_insights(self, query_run_id: uuid.UUID, payload: InsightsPayload) -> None:
        del query_run_id
        self._cached = payload


def _session() -> SessionRecord:
    now = datetime.now(UTC)
    return SessionRecord(
        id=uuid.uuid4(),
        token_hash="h",
        created_at=now,
        expires_at=now + timedelta(hours=24),
        status="active",
    )


async def test_generate_insights_caches_result_and_enforces_ownership() -> None:
    owner = _session()
    intruder = _session()
    run = QueryRunSummary(
        id=uuid.uuid4(),
        question="Revenue by region",
        generated_sql="SELECT region, SUM(revenue) FROM retail_sales GROUP BY region",
        row_count=4,
    )
    repo = FakeInsightsRepository(owner.id, run)
    llm = FakeLLM(
        InsightsPayload(
            summary="North leads with 520.0 in revenue.",
            key_findings=["North: 520.0", "South: 645.0"],
            next_questions=["Break down revenue by product category"],
        )
    )
    service = InsightsService(repo, llm)

    first = await service.generate(owner, run.id)
    assert first.summary == "North leads with 520.0 in revenue."
    assert llm.calls == 1

    second = await service.generate(owner, run.id)
    assert second == first
    assert llm.calls == 1

    with pytest.raises(NotFound):
        await service.generate(intruder, run.id)
