"""HTTP router for insights."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])
