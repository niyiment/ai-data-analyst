"""Database repository for query_runs and dataset schema lookup."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import DatasetModel, DatasetTableModel, QueryRunModel
from app.query.schemas import QueryHistoryItem


@dataclass(frozen=True)
class DatasetQueryContext:
    """Dataset schema metadata needed to build prompts and validate SQL."""

    dataset_id: uuid.UUID
    schema_name: str
    table_names: frozenset[str]
    schema_summary: str


@dataclass(frozen=True)
class QueryRunCreate:
    """Typed payload for persisting a completed or rejected query run."""

    id: uuid.UUID
    session_id: uuid.UUID
    dataset_id: uuid.UUID
    question: str
    plan: dict[str, Any] | None
    generated_sql: str | None
    validation_status: str
    rejection_reasons: list[dict[str, str]] | None
    status: str
    error_code: str | None
    row_count: int
    truncated: bool
    stage_timings_ms: dict[str, int]
    created_at: datetime


class QueryRepository(Protocol):
    """Repository interface for query runs and dataset schema lookup."""

    async def get_dataset_context(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID
    ) -> DatasetQueryContext | None: ...

    async def get_recent_questions(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID, limit: int = 3
    ) -> list[tuple[str, dict[str, Any] | None]]: ...

    async def save_run(self, payload: QueryRunCreate) -> None: ...

    async def list_history(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[QueryHistoryItem], int]: ...


class SqlQueryRepository:
    """PostgreSQL-backed query repository."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_dataset_context(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID
    ) -> DatasetQueryContext | None:
        stmt = (
            select(DatasetModel)
            .options(selectinload(DatasetModel.tables).selectinload(DatasetTableModel.columns))
            .where(DatasetModel.id == dataset_id, DatasetModel.session_id == session_id)
        )
        model = (await self._db.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        lines: list[str] = []
        table_names: set[str] = set()
        for tbl in model.tables:
            table_names.add(tbl.table_name)
            cols = ", ".join(f"{c.column_name} ({c.pg_type})" for c in tbl.columns)
            lines.append(f"Table {tbl.table_name} ({tbl.row_count} rows): {cols}")
        return DatasetQueryContext(
            dataset_id=model.id,
            schema_name=model.schema_name,
            table_names=frozenset(table_names),
            schema_summary="\n".join(lines),
        )

    async def get_recent_questions(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID, limit: int = 3
    ) -> list[tuple[str, dict[str, Any] | None]]:
        stmt = (
            select(QueryRunModel.question, QueryRunModel.plan)
            .where(
                QueryRunModel.session_id == session_id,
                QueryRunModel.dataset_id == dataset_id,
            )
            .order_by(QueryRunModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._db.execute(stmt)).all()
        return [(q, p) for q, p in reversed(rows)]

    async def save_run(self, payload: QueryRunCreate) -> None:
        model = QueryRunModel(
            id=payload.id,
            session_id=payload.session_id,
            dataset_id=payload.dataset_id,
            question=payload.question,
            plan=payload.plan,
            generated_sql=payload.generated_sql,
            validation_status=payload.validation_status,
            rejection_reasons=payload.rejection_reasons,
            status=payload.status,
            error_code=payload.error_code,
            row_count=payload.row_count,
            truncated=payload.truncated,
            stage_timings_ms=payload.stage_timings_ms,
            created_at=payload.created_at,
        )
        self._db.add(model)
        await self._db.commit()

    async def list_history(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[QueryHistoryItem], int]:
        where = (
            QueryRunModel.session_id == session_id,
            QueryRunModel.dataset_id == dataset_id,
        )
        total = (
            await self._db.execute(select(func.count()).select_from(QueryRunModel).where(*where))
        ).scalar_one()
        stmt = (
            select(QueryRunModel)
            .where(*where)
            .order_by(QueryRunModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = list((await self._db.execute(stmt)).scalars().all())
        items = [
            QueryHistoryItem(
                id=m.id,
                question=m.question,
                status=m.status,
                generated_sql=m.generated_sql,
                row_count=m.row_count,
                created_at=m.created_at,
            )
            for m in models
        ]
        return items, int(total)
