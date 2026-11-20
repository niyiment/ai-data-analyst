"""Pydantic schemas for sessions."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class SessionRecord(BaseModel):
    """Internal typed representation of a persisted session."""

    id: uuid.UUID
    token_hash: str
    created_at: datetime
    expires_at: datetime
    status: str


class SessionResponse(BaseModel):
    """Public session status returned to the browser (never includes the token)."""

    session_id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    status: str


class DeleteSessionResponse(BaseModel):
    """Confirmation returned when a user deletes their session data."""

    deleted: bool
    schemas_dropped: int


class CleanupResponse(BaseModel):
    """Summary returned by the scheduled cleanup endpoint."""

    sessions_deleted: int
    schemas_dropped: int
