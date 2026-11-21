"""FastAPI dependencies for the evaluation module."""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session, get_session_factory
from app.evaluation.repository import EvalRepository, SqlEvalRepository
from app.evaluation.runner import LlmEvalRunner
from app.evaluation.schemas import EvalRunDetail, GoldenSet
from app.evaluation.service import EvaluationService
from app.llm.factory import describe_llm, get_llm_client
from app.llm.port import LLMClient
from app.query.executor import PostgresReadOnlyExecutor

EvalJob = Callable[[EvalRunDetail], Awaitable[None]]


def _build_service(
    repo: EvalRepository, settings: Settings, llm: LLMClient, model_label: str
) -> EvaluationService:
    executor = PostgresReadOnlyExecutor(
        settings.database_url_analyst,
        timeout_seconds=settings.query_timeout_seconds,
        max_rows=settings.max_rows,
    )

    def build_runner(golden_set: GoldenSet) -> LlmEvalRunner:
        return LlmEvalRunner(golden_set, llm=llm, executor=executor)

    return EvaluationService(repo=repo, runner_factory=build_runner, model_name=model_label)


def get_eval_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
    x_llm_provider: Annotated[str | None, Header()] = None,
    x_llm_model: Annotated[str | None, Header()] = None,
) -> EvaluationService:
    """Wire the real LLM runner, read-only executor, and PostgreSQL run store."""
    label = describe_llm(settings, provider=x_llm_provider, model=x_llm_model)
    return _build_service(SqlEvalRepository(db), settings, llm, label)


def get_eval_job(
    settings: Annotated[Settings, Depends(get_settings)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
) -> EvalJob:
    """Background job that executes a started run with its own database session.

    The request's session is closed before background tasks run, so the job opens one.
    """

    async def job(run: EvalRunDetail) -> None:
        async with get_session_factory()() as db:
            service = _build_service(SqlEvalRepository(db), settings, llm, run.model)
            await service.execute_run(run)

    return job
