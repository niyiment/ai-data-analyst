"""HTTP router for natural-language queries and history."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.query.dependencies import enforce_question_rate_limit, get_query_service
from app.query.schemas import QueryHistoryResponse, QueryRequest, QueryResponse
from app.query.service import QueryService
from app.sessions.dependencies import require_session
from app.sessions.schemas import SessionRecord

router = APIRouter(prefix="/api/v1/datasets", tags=["query"])


@router.post(
    "/{dataset_id}/queries",
    response_model=QueryResponse,
    dependencies=[Depends(enforce_question_rate_limit)],
)
async def ask_question(
    dataset_id: uuid.UUID,
    payload: QueryRequest,
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[QueryService, Depends(get_query_service)],
) -> QueryResponse:
    """Ask a natural-language question against a dataset."""
    return await service.ask(session, dataset_id, payload)


@router.get("/{dataset_id}/queries", response_model=QueryHistoryResponse)
async def list_query_history(
    dataset_id: uuid.UUID,
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[QueryService, Depends(get_query_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> QueryHistoryResponse:
    """Return paginated question history for a dataset."""
    return await service.list_history(session, dataset_id, limit=limit, offset=offset)
