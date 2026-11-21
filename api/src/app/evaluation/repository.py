"""Repositories for storing and retrieving evaluation runs."""

from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.evaluation.models import EvalRunModel
from app.evaluation.schemas import EvalRunDetail


class EvalRepository(Protocol):
    """Persistence port for evaluation runs."""

    async def save_run(self, run: EvalRunDetail) -> EvalRunDetail: ...

    async def get_run(self, run_id: UUID) -> EvalRunDetail | None: ...


def run_to_model(run: EvalRunDetail) -> EvalRunModel:
    """Map a run to its ORM row, keeping the full detail as JSON."""
    return EvalRunModel(
        id=run.id,
        set_name=run.set_name,
        model=run.model,
        prompt_version=run.prompt_version,
        started_at=run.started_at,
        finished_at=run.finished_at,
        accuracy=run.accuracy,
        status=run.status,
        error=run.error,
        detail=run.model_dump(mode="json"),
    )


def model_to_run(model: EvalRunModel) -> EvalRunDetail:
    """Rebuild a typed run from its ORM row."""
    return EvalRunDetail.model_validate(model.detail)


class InMemoryEvalRepository:
    """In-memory store for tests and local experiments."""

    def __init__(self) -> None:
        self._runs: dict[UUID, EvalRunDetail] = {}

    async def save_run(self, run: EvalRunDetail) -> EvalRunDetail:
        """Persist an evaluation run."""
        self._runs[run.id] = run
        return run

    async def get_run(self, run_id: UUID) -> EvalRunDetail | None:
        """Return a stored evaluation run by ID, or None."""
        return self._runs.get(run_id)


class SqlEvalRepository:
    """PostgreSQL-backed store in app.eval_runs."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def save_run(self, run: EvalRunDetail) -> EvalRunDetail:
        """Insert or update the run (progress is saved repeatedly) and commit."""
        await self._db.merge(run_to_model(run))
        await self._db.commit()
        return run

    async def get_run(self, run_id: UUID) -> EvalRunDetail | None:
        """Load a run by primary key, or None."""
        model = await self._db.get(EvalRunModel, run_id)
        return model_to_run(model) if model is not None else None
