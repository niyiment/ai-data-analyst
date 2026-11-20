"""FastAPI dependencies for the query module."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.llm.factory import get_llm_client
from app.llm.port import LLMClient
from app.query.executor import PostgresReadOnlyExecutor
from app.query.repository import SqlQueryRepository
from app.query.service import QueryService


def get_query_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
) -> QueryService:
    """Construct a QueryService wired with PostgreSQL, the chosen LLM, and the executor."""
    return QueryService(
        repo=SqlQueryRepository(db),
        llm=llm,
        executor=PostgresReadOnlyExecutor(
            settings.database_url_analyst,
            timeout_seconds=settings.query_timeout_seconds,
            max_rows=settings.max_rows,
        ),
    )
