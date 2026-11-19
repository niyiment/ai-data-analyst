"""HTTP router for reports."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
