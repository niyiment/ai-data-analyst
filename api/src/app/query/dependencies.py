"""FastAPI dependencies for the query module."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.rate_limit import RateLimiter
from app.llm.factory import get_llm_client
from app.llm.port import LLMClient
from app.query.executor import PostgresReadOnlyExecutor
from app.query.repository import SqlQueryRepository
from app.query.service import QueryService
from app.sessions.dependencies import require_session
from app.sessions.schemas import SessionRecord


@lru_cache(maxsize=1)
def get_question_rate_limiter() -> RateLimiter:
    """Return the shared per-session hourly question limiter."""
    return RateLimiter(limit=get_settings().questions_per_session_per_hour, window_seconds=3600)


def enforce_question_rate_limit(
    session: Annotated[SessionRecord, Depends(require_session)],
    limiter: Annotated[RateLimiter, Depends(get_question_rate_limiter)],
) -> None:
    """Reject the request with RATE_LIMITED once the session's hourly budget is spent."""
    limiter.check(str(session.id))


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
