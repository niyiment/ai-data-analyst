"""HTTP endpoints for golden-set evaluation (docs/API.md)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.core.rate_limit import RateLimiter
from app.evaluation.schemas import EvalRunCreate, EvalRunDetail, GoldenSetSummary
from app.evaluation.service import EvaluationService, get_default_eval_service

router = APIRouter(prefix="/api/v1/eval", tags=["evaluation"])

_eval_rate_limiter = RateLimiter(limit=5, window_seconds=60)
EvalServiceDep = Annotated[EvaluationService, Depends(get_default_eval_service)]


@router.get("/sets", response_model=list[GoldenSetSummary])
async def list_eval_sets(service: EvalServiceDep) -> list[GoldenSetSummary]:
    """List available golden evaluation sets."""
    return service.list_sets()


@router.post("/runs", response_model=EvalRunDetail, status_code=status.HTTP_201_CREATED)
async def start_eval_run(
    payload: EvalRunCreate,
    request: Request,
    service: EvalServiceDep,
) -> EvalRunDetail:
    """Run a golden evaluation set (rate limited per client IP)."""
    client_key = request.client.host if request.client else "unknown"
    _eval_rate_limiter.check(client_key)
    return await service.run_evaluation(payload.set_name)


@router.get("/runs/{run_id}", response_model=EvalRunDetail)
async def get_eval_run(run_id: UUID, service: EvalServiceDep) -> EvalRunDetail:
    """Retrieve results for a completed evaluation run."""
    return service.get_run(run_id)
