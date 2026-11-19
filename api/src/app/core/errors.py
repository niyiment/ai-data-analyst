"""Domain exception hierarchy and standard API error response."""

from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error envelope returned by every API endpoint."""

    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str


class DomainError(Exception):
    """Base class for domain errors mapped by the global exception handler."""

    status_code: int = 400
    code: str = "DOMAIN_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationRejected(DomainError):
    """Raised when SQL or input validation fails closed."""

    status_code = 422
    code = "VALIDATION_REJECTED"


class QuotaExceeded(DomainError):
    """Raised when rate limit or LLM quota is exceeded."""

    status_code = 429
    code = "QUOTA_EXCEEDED"


class NotFound(DomainError):
    """Raised when a requested resource does not exist."""

    status_code = 404
    code = "NOT_FOUND"


class Forbidden(DomainError):
    """Raised when a session is not permitted to access a resource."""

    status_code = 403
    code = "FORBIDDEN"


class SessionExpired(DomainError):
    """Raised when a session cookie is missing, invalid, or expired."""

    status_code = 401
    code = "SESSION_EXPIRED"


class FileTooLarge(DomainError):
    """Raised when an uploaded file exceeds MAX_UPLOAD_MB."""

    status_code = 413
    code = "FILE_TOO_LARGE"


class UnsupportedFile(DomainError):
    """Raised when an uploaded file is not a valid CSV or XLSX."""

    status_code = 400
    code = "UNSUPPORTED_FILE"


class QueryTimeout(DomainError):
    """Raised when a read-only SQL query exceeds the statement timeout."""

    status_code = 504
    code = "QUERY_TIMEOUT"
