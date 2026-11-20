"""Repository for storing and retrieving evaluation runs."""

from uuid import UUID

from app.evaluation.schemas import EvalRunDetail


class InMemoryEvalRepository:
    """In-memory store for evaluation runs (swappable with DB repository)."""

    def __init__(self) -> None:
        self._runs: dict[UUID, EvalRunDetail] = {}

    def save_run(self, run: EvalRunDetail) -> EvalRunDetail:
        """Persist an evaluation run."""
        self._runs[run.id] = run
        return run

    def get_run(self, run_id: UUID) -> EvalRunDetail | None:
        """Return a stored evaluation run by ID, or None."""
        return self._runs.get(run_id)
