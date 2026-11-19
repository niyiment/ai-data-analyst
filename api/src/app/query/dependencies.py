"""FastAPI dependencies for the query module."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.llm.gemini import GeminiLLMClient
from app.query.executor import PostgresReadOnlyExecutor
from app.query.repository import SqlQueryRepository
from app.query.service import QueryService


def get_query_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> QueryService:
    """Construct a QueryService wired with PostgreSQL, Gemini, and the read-only executor."""
    return QueryService(
        repo=SqlQueryRepository(db),
        llm=GeminiLLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model),
        executor=PostgresReadOnlyExecutor(
            settings.database_url_analyst,
            timeout_seconds=settings.query_timeout_seconds,
            max_rows=settings.max_rows,
        ),
    )
