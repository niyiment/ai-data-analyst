"""HTTP router for datasets."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])
