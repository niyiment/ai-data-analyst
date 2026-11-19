"""HTTP router for charts."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/charts", tags=["charts"])
