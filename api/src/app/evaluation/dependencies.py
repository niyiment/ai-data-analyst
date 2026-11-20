"""FastAPI dependencies for the evaluation module."""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.evaluation.repository import SqlEvalRepository
from app.evaluation.runner import LlmEvalRunner
from app.evaluation.schemas import GoldenSet
from app.evaluation.service import EvaluationService
from app.llm.factory import describe_llm, get_llm_client
from app.llm.port import LLMClient
from app.query.executor import PostgresReadOnlyExecutor


def get_eval_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
    x_llm_provider: Annotated[str | None, Header()] = None,
    x_llm_model: Annotated[str | None, Header()] = None,
) -> EvaluationService:
    """Wire the real LLM runner, read-only executor, and PostgreSQL run store."""
    executor = PostgresReadOnlyExecutor(
        settings.database_url_analyst,
        timeout_seconds=settings.query_timeout_seconds,
        max_rows=settings.max_rows,
    )

    def build_runner(golden_set: GoldenSet) -> LlmEvalRunner:
        return LlmEvalRunner(golden_set, llm=llm, executor=executor)

    return EvaluationService(
        repo=SqlEvalRepository(db),
        runner_factory=build_runner,
        model_name=describe_llm(settings, provider=x_llm_provider, model=x_llm_model),
    )
