"""Business logic service for anonymous cookie sessions and cleanup."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from app.core.errors import Forbidden, SessionExpired
from app.sessions.repository import SessionRepository
from app.sessions.schemas import (
    CleanupResponse,
    DeleteSessionResponse,
    SessionRecord,
    SessionResponse,
)


def hash_token(token: str) -> str:
    """Return a SHA-256 hex digest of an opaque session token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class SessionService:
    """Manages anonymous session lifecycle, lazy expiry, and scheduled cleanup."""

    def __init__(
        self,
        repo: SessionRepository,
        *,
        ttl_hours: int = 24,
        cleanup_secret: str = "",
    ) -> None:
        self._repo = repo
        self._ttl = timedelta(hours=ttl_hours)
        self._cleanup_secret = cleanup_secret

    async def create_session(self, *, ip_hash: str | None = None) -> tuple[str, SessionResponse]:
        """Issue a new opaque token and persist only its hash."""
        raw_token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        record = await self._repo.create(
            token_hash=hash_token(raw_token),
            created_at=now,
            expires_at=now + self._ttl,
            ip_hash=ip_hash,
        )
        return raw_token, _to_response(record)

    async def get_active_session(self, raw_token: str | None) -> SessionRecord:
        """Resolve an active session from a cookie token, enforcing lazy expiry."""
        if not raw_token:
            raise SessionExpired("No active session found.")
        record = await self._repo.get_by_token_hash(hash_token(raw_token))
        if record is None:
            raise SessionExpired("Session not found or already deleted.")
        if record.expires_at <= datetime.now(UTC):
            await self._repo.delete_session_and_schemas(record.id)
            raise SessionExpired("Session has expired and its data was deleted.")
        return record

    async def get_session_response(self, raw_token: str | None) -> SessionResponse:
        """Return public session metadata for the current cookie."""
        record = await self.get_active_session(raw_token)
        return _to_response(record)

    async def delete_current_session(self, raw_token: str | None) -> DeleteSessionResponse:
        """Delete the caller's session and all its dataset schemas immediately."""
        record = await self.get_active_session(raw_token)
        dropped = await self._repo.delete_session_and_schemas(record.id)
        return DeleteSessionResponse(deleted=True, schemas_dropped=dropped)

    async def run_scheduled_cleanup(self, provided_secret: str | None) -> CleanupResponse:
        """Purge all expired sessions when authorised by the shared cleanup secret."""
        if not self._cleanup_secret or not provided_secret:
            raise Forbidden("Invalid cleanup credentials.")
        if not hmac.compare_digest(provided_secret, self._cleanup_secret):
            raise Forbidden("Invalid cleanup credentials.")
        sessions_deleted, schemas_dropped = await self._repo.purge_expired(datetime.now(UTC))
        return CleanupResponse(
            sessions_deleted=sessions_deleted,
            schemas_dropped=schemas_dropped,
        )


def _to_response(record: SessionRecord) -> SessionResponse:
    return SessionResponse(
        session_id=record.id,
        created_at=record.created_at,
        expires_at=record.expires_at,
        status=record.status,
    )
