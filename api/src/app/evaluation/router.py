"""HTTP endpoints for golden-set evaluation (docs/API.md)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

from app.core.rate_limit import RateLimiter
from app.evaluation.dependencies import EvalJob, get_eval_job, get_eval_service
from app.evaluation.schemas import EvalRunCreate, EvalRunDetail, GoldenSetSummary
from app.evaluation.service import EvaluationService

router = APIRouter(prefix="/api/v1/eval", tags=["evaluation"])

_eval_rate_limiter = RateLimiter(limit=5, window_seconds=60)
EvalServiceDep = Annotated[EvaluationService, Depends(get_eval_service)]


@router.get("/sets", response_model=list[GoldenSetSummary])
async def list_eval_sets(service: EvalServiceDep) -> list[GoldenSetSummary]:
    """List available golden evaluation sets."""
    return service.list_sets()


@router.post("/runs", response_model=EvalRunDetail, status_code=status.HTTP_202_ACCEPTED)
async def start_eval_run(
    payload: EvalRunCreate,
    request: Request,
    background: BackgroundTasks,
    service: EvalServiceDep,
    job: Annotated[EvalJob, Depends(get_eval_job)],
) -> EvalRunDetail:
    """Start a run (rate limited per client IP); poll GET /runs/{id} for progress."""
    client_key = request.client.host if request.client else "unknown"
    _eval_rate_limiter.check(client_key)
    run = await service.start_run(payload.set_name)
    background.add_task(job, run)
    return run


@router.get("/runs/{run_id}", response_model=EvalRunDetail)
async def get_eval_run(run_id: UUID, service: EvalServiceDep) -> EvalRunDetail:
    """Retrieve a run: running (with results so far), completed, or failed."""
    return await service.get_run(run_id)
