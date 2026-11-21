"""API tests for the per-session question rate limit (US-15)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.rate_limit import RateLimiter
from app.main import create_app
from app.query.dependencies import get_query_service, get_question_rate_limiter
from app.query.schemas import QueryRequest, QueryResponse
from app.sessions.dependencies import require_session
from app.sessions.schemas import SessionRecord


def _session() -> SessionRecord:
    now = datetime.now(UTC)
    return SessionRecord(
        id=uuid.uuid4(),
        token_hash="hash",
        created_at=now,
        expires_at=now + timedelta(hours=24),
        status="active",
    )


class FakeQueryService:
    """Counts questions instead of calling the LLM or database."""

    def __init__(self) -> None:
        self.asked = 0

    async def ask(
        self, session: SessionRecord, dataset_id: uuid.UUID, payload: QueryRequest
    ) -> QueryResponse:
        self.asked += 1
        raise AssertionError("service must not run once the limit is hit")


@pytest.mark.asyncio
async def test_question_over_session_limit_returns_429_with_retry_time() -> None:
    app = create_app()
    service = FakeQueryService()
    session = _session()
    limiter = RateLimiter(limit=1, window_seconds=3600)
    limiter.check(str(session.id))  # this session has already used its only question
    app.dependency_overrides[require_session] = lambda: session
    app.dependency_overrides[get_query_service] = lambda: service
    app.dependency_overrides[get_question_rate_limiter] = lambda: limiter

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/datasets/{uuid.uuid4()}/queries", json={"question": "How many orders?"}
        )

    assert resp.status_code == 429
    body = resp.json()
    assert body["code"] == "RATE_LIMITED"
    assert body["details"]["retry_after_seconds"] > 0
    assert service.asked == 0


def test_question_limiter_is_a_shared_singleton() -> None:
    limiter = get_question_rate_limiter()

    assert isinstance(limiter, RateLimiter)
    assert limiter is get_question_rate_limiter()
