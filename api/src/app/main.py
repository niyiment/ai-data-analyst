"""FastAPI application entrypoint."""

import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.errors import DomainError, ErrorResponse
from app.core.logging import configure_logging
from app.datasets.router import router as datasets_router
from app.insights.router import router as insights_router
from app.query.router import router as query_router
from app.reports.router import router as reports_router
from app.sessions.router import internal_router as sessions_internal_router
from app.sessions.router import router as sessions_router


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(title="AI Data Analyst API", version="0.1.0")

    @application.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        body = ErrorResponse(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    application.include_router(sessions_router)
    application.include_router(sessions_internal_router)
    application.include_router(datasets_router)
    application.include_router(query_router)
    application.include_router(insights_router)
    application.include_router(reports_router)

    return application


app = create_app()
