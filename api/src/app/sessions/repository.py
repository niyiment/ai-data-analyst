"""Database repository for sessions and schema cleanup."""

import uuid
from datetime import datetime
from typing import Protocol

from psycopg import sql
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import DatasetModel, SessionModel
from app.sessions.schemas import SessionRecord


class SessionRepository(Protocol):
    """Repository interface for session persistence and cleanup."""

    async def create(
        self,
        *,
        token_hash: str,
        created_at: datetime,
        expires_at: datetime,
        ip_hash: str | None = None,
    ) -> SessionRecord: ...

    async def get_by_token_hash(self, token_hash: str) -> SessionRecord | None: ...

    async def delete_session_and_schemas(self, session_id: uuid.UUID) -> int: ...

    async def purge_expired(self, now: datetime) -> tuple[int, int]: ...


class SqlSessionRepository:
    """PostgreSQL-backed session repository."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        token_hash: str,
        created_at: datetime,
        expires_at: datetime,
        ip_hash: str | None = None,
    ) -> SessionRecord:
        model = SessionModel(
            id=uuid.uuid4(),
            token_hash=token_hash,
            created_at=created_at,
            expires_at=expires_at,
            status="active",
            ip_hash=ip_hash,
        )
        self._db.add(model)
        await self._db.commit()
        return _to_record(model)

    async def get_by_token_hash(self, token_hash: str) -> SessionRecord | None:
        stmt = select(SessionModel).where(SessionModel.token_hash == token_hash)
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_record(model) if model is not None else None

    async def delete_session_and_schemas(self, session_id: uuid.UUID) -> int:
        schemas = await self._drop_schemas_for_session(session_id)
        await self._db.execute(delete(SessionModel).where(SessionModel.id == session_id))
        await self._db.commit()
        return schemas

    async def purge_expired(self, now: datetime) -> tuple[int, int]:
        stmt = select(SessionModel.id).where(SessionModel.expires_at <= now)
        expired_ids = list((await self._db.execute(stmt)).scalars().all())
        schemas_dropped = 0
        for sid in expired_ids:
            schemas_dropped += await self._drop_schemas_for_session(sid)
            await self._db.execute(delete(SessionModel).where(SessionModel.id == sid))
        if expired_ids:
            await self._db.commit()
        return len(expired_ids), schemas_dropped

    async def _drop_schemas_for_session(self, session_id: uuid.UUID) -> int:
        stmt = select(DatasetModel.schema_name).where(DatasetModel.session_id == session_id)
        schema_names = list((await self._db.execute(stmt)).scalars().all())
        raw_conn = await self._db.connection()
        driver_conn = await raw_conn.get_raw_connection()
        for schema_name in schema_names:
            drop_stmt = sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                sql.Identifier(schema_name)
            )
            async with driver_conn.driver_connection.cursor() as cur:  # type: ignore[union-attr]
                await cur.execute(drop_stmt)
        return len(schema_names)


def _to_record(model: SessionModel) -> SessionRecord:
    return SessionRecord(
        id=model.id,
        token_hash=model.token_hash,
        created_at=model.created_at,
        expires_at=model.expires_at,
        status=model.status,
    )
