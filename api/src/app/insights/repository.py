"""Database repository for on-demand query insights."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import QueryArtifactModel, QueryRunModel
from app.insights.schemas import InsightsPayload


@dataclass(frozen=True)
class QueryRunSummary:
    """Minimal query run metadata needed to generate insights."""

    id: uuid.UUID
    question: str
    generated_sql: str | None
    row_count: int


class InsightsRepository(Protocol):
    """Repository interface for insights lookup and persistence."""

    async def get_query_run(
        self, session_id: uuid.UUID, query_run_id: uuid.UUID
    ) -> QueryRunSummary | None: ...

    async def get_cached_insights(self, query_run_id: uuid.UUID) -> InsightsPayload | None: ...

    async def save_insights(self, query_run_id: uuid.UUID, payload: InsightsPayload) -> None: ...


class SqlInsightsRepository:
    """PostgreSQL-backed insights repository."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_query_run(
        self, session_id: uuid.UUID, query_run_id: uuid.UUID
    ) -> QueryRunSummary | None:
        stmt = select(QueryRunModel).where(
            QueryRunModel.id == query_run_id,
            QueryRunModel.session_id == session_id,
        )
        model = (await self._db.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return QueryRunSummary(
            id=model.id,
            question=model.question,
            generated_sql=model.generated_sql,
            row_count=model.row_count,
        )

    async def get_cached_insights(self, query_run_id: uuid.UUID) -> InsightsPayload | None:
        stmt = select(QueryArtifactModel).where(
            QueryArtifactModel.query_run_id == query_run_id,
            QueryArtifactModel.kind == "insights",
            QueryArtifactModel.is_valid.is_(True),
        )
        model = (await self._db.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return InsightsPayload.model_validate(model.content)

    async def save_insights(self, query_run_id: uuid.UUID, payload: InsightsPayload) -> None:
        artifact = QueryArtifactModel(
            id=uuid.uuid4(),
            query_run_id=query_run_id,
            kind="insights",
            content=payload.model_dump(),
            is_valid=True,
        )
        self._db.add(artifact)
        await self._db.commit()
