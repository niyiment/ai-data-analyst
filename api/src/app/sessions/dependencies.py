"""FastAPI dependencies for session resolution and service injection."""

from typing import Annotated

from fastapi import Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.sessions.repository import SqlSessionRepository
from app.sessions.schemas import SessionRecord
from app.sessions.service import SessionService

SESSION_COOKIE_NAME = "ada_session"


def get_session_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SessionService:
    """Construct a SessionService backed by PostgreSQL."""
    return SessionService(
        SqlSessionRepository(db),
        ttl_hours=settings.session_ttl_hours,
        cleanup_secret=settings.cleanup_secret,
    )


def set_session_cookie(response: Response, token: str, ttl_hours: int) -> None:
    """Attach the opaque session token as a Secure, HttpOnly, SameSite=Lax cookie."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ttl_hours * 3600,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Expire the session cookie on the client."""
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


async def require_session(
    service: Annotated[SessionService, Depends(get_session_service)],
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> SessionRecord:
    """Resolve and validate the current session from the HttpOnly cookie."""
    return await service.get_active_session(session_token)
