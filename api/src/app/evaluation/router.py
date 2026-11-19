"""HTTP router for evaluation."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])
