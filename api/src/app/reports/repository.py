"""Database repository for reports and pinned report items."""

import uuid
from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import QueryRunModel, ReportItemModel, ReportModel
from app.reports.schemas import ReportItemInput, ReportItemView, ReportResponse


class ReportRepository(Protocol):
    """Repository interface for reports."""

    async def create_report(
        self,
        *,
        session_id: uuid.UUID,
        title: str,
        items: list[ReportItemInput],
        created_at: datetime,
    ) -> ReportResponse: ...

    async def get_report(
        self, session_id: uuid.UUID, report_id: uuid.UUID
    ) -> ReportResponse | None: ...


class SqlReportRepository:
    """PostgreSQL-backed report repository."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_report(
        self,
        *,
        session_id: uuid.UUID,
        title: str,
        items: list[ReportItemInput],
        created_at: datetime,
    ) -> ReportResponse:
        report = ReportModel(
            id=uuid.uuid4(),
            session_id=session_id,
            title=title,
            created_at=created_at,
        )
        for pos, item in enumerate(items):
            report.items.append(
                ReportItemModel(
                    id=uuid.uuid4(),
                    query_run_id=item.query_run_id,
                    position=pos,
                    note=item.note,
                )
            )
        self._db.add(report)
        await self._db.commit()
        hydrated = await self.get_report(session_id, report.id)
        assert hydrated is not None
        return hydrated

    async def get_report(
        self, session_id: uuid.UUID, report_id: uuid.UUID
    ) -> ReportResponse | None:
        stmt = (
            select(ReportModel)
            .options(selectinload(ReportModel.items))
            .where(ReportModel.id == report_id, ReportModel.session_id == session_id)
        )
        model = (await self._db.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None

        run_ids = [item.query_run_id for item in model.items]
        runs_map: dict[uuid.UUID, QueryRunModel] = {}
        if run_ids:
            runs_stmt = select(QueryRunModel).where(
                QueryRunModel.id.in_(run_ids), QueryRunModel.session_id == session_id
            )
            for run in (await self._db.execute(runs_stmt)).scalars().all():
                runs_map[run.id] = run

        views = [_to_item_view(item, runs_map.get(item.query_run_id)) for item in model.items]
        return ReportResponse(
            id=model.id,
            title=model.title,
            created_at=model.created_at,
            items=views,
        )


def _to_item_view(item: ReportItemModel, run: QueryRunModel | None) -> ReportItemView:
    return ReportItemView(
        id=item.id,
        query_run_id=item.query_run_id,
        position=item.position,
        question=run.question if run else "",
        generated_sql=run.generated_sql if run else None,
        note=item.note,
    )
