"""HTTP router for query."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/query", tags=["query"])
