"""HTTP router for on-demand query insights (US-12)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.insights.dependencies import get_insights_service
from app.insights.schemas import InsightsPayload
from app.insights.service import InsightsService
from app.sessions.dependencies import require_session
from app.sessions.schemas import SessionRecord

router = APIRouter(prefix="/api/v1/queries", tags=["insights"])


@router.post("/{query_run_id}/insights", response_model=InsightsPayload)
async def generate_insights(
    query_run_id: uuid.UUID,
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[InsightsService, Depends(get_insights_service)],
) -> InsightsPayload:
    """Generate grounded insights on demand for a completed query run."""
    return await service.generate(session, query_run_id)
