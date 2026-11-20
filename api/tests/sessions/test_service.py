"""Unit tests for SessionService (US-01, US-02, US-03)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.errors import Forbidden, SessionExpired
from app.sessions.schemas import SessionRecord
from app.sessions.service import SessionService, hash_token


class FakeSessionRepository:
    """In-memory SessionRepository fake for unit tests."""

    def __init__(self) -> None:
        self.sessions: dict[uuid.UUID, SessionRecord] = {}
        self.schemas_per_session: dict[uuid.UUID, int] = {}

    async def create(
        self,
        *,
        token_hash: str,
        created_at: datetime,
        expires_at: datetime,
        ip_hash: str | None = None,
    ) -> SessionRecord:
        record = SessionRecord(
            id=uuid.uuid4(),
            token_hash=token_hash,
            created_at=created_at,
            expires_at=expires_at,
            status="active",
        )
        self.sessions[record.id] = record
        return record

    async def get_by_token_hash(self, token_hash: str) -> SessionRecord | None:
        for record in self.sessions.values():
            if record.token_hash == token_hash:
                return record
        return None

    async def delete_session_and_schemas(self, session_id: uuid.UUID) -> int:
        self.sessions.pop(session_id, None)
        return self.schemas_per_session.pop(session_id, 0)

    async def purge_expired(self, now: datetime) -> tuple[int, int]:
        expired = [sid for sid, rec in self.sessions.items() if rec.expires_at <= now]
        dropped = 0
        for sid in expired:
            dropped += await self.delete_session_and_schemas(sid)
        return len(expired), dropped


async def test_create_session_stores_only_hash() -> None:
    repo = FakeSessionRepository()
    service = SessionService(repo, ttl_hours=24)

    raw_token, response = await service.create_session()

    assert raw_token not in response.model_dump_json()
    stored = repo.sessions[response.session_id]
    assert stored.token_hash == hash_token(raw_token)
    assert stored.token_hash != raw_token


async def test_lazy_expiry_rejects_and_purges_expired_session() -> None:
    repo = FakeSessionRepository()
    service = SessionService(repo, ttl_hours=24)
    raw_token, response = await service.create_session()
    repo.schemas_per_session[response.session_id] = 2
    repo.sessions[response.session_id] = repo.sessions[response.session_id].model_copy(
        update={"expires_at": datetime.now(UTC) - timedelta(seconds=1)}
    )

    with pytest.raises(SessionExpired):
        await service.get_active_session(raw_token)

    assert response.session_id not in repo.sessions


async def test_delete_current_session_removes_data_immediately() -> None:
    repo = FakeSessionRepository()
    service = SessionService(repo, ttl_hours=24)
    raw_token, response = await service.create_session()
    repo.schemas_per_session[response.session_id] = 3

    result = await service.delete_current_session(raw_token)

    assert result.deleted is True
    assert result.schemas_dropped == 3
    assert response.session_id not in repo.sessions


async def test_scheduled_cleanup_requires_valid_secret() -> None:
    repo = FakeSessionRepository()
    service = SessionService(repo, ttl_hours=24, cleanup_secret="top-secret")

    with pytest.raises(Forbidden):
        await service.run_scheduled_cleanup("wrong-secret")

    result = await service.run_scheduled_cleanup("top-secret")
    assert result.sessions_deleted == 0
