"""HTTP router for sessions and internal scheduled cleanup."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, Response

from app.core.config import Settings, get_settings
from app.sessions.dependencies import (
    SESSION_COOKIE_NAME,
    clear_session_cookie,
    get_session_service,
    set_session_cookie,
)
from app.sessions.schemas import CleanupResponse, DeleteSessionResponse, SessionResponse
from app.sessions.service import SessionService

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
internal_router = APIRouter(prefix="/api/v1/internal", tags=["internal"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    response: Response,
    service: Annotated[SessionService, Depends(get_session_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SessionResponse:
    """Create a new anonymous session and set its HttpOnly cookie."""
    token, session_response = await service.create_session()
    set_session_cookie(response, token, settings.session_ttl_hours)
    return session_response


@router.get("/me", response_model=SessionResponse)
async def get_my_session(
    service: Annotated[SessionService, Depends(get_session_service)],
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> SessionResponse:
    """Return the active session's status and expiry time."""
    return await service.get_session_response(session_token)


@router.delete("/me", response_model=DeleteSessionResponse)
async def delete_my_session(
    response: Response,
    service: Annotated[SessionService, Depends(get_session_service)],
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> DeleteSessionResponse:
    """Delete the caller's session and all owned dataset schemas immediately."""
    result = await service.delete_current_session(session_token)
    clear_session_cookie(response)
    return result


@internal_router.post("/cleanup", response_model=CleanupResponse)
async def run_cleanup(
    service: Annotated[SessionService, Depends(get_session_service)],
    x_cleanup_secret: Annotated[str | None, Header()] = None,
) -> CleanupResponse:
    """Purge expired sessions and their schemas (authenticated by shared secret)."""
    return await service.run_scheduled_cleanup(x_cleanup_secret)
