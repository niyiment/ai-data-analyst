"""FastAPI dependencies for the datasets module."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.datasets.repository import SqlDatasetRepository
from app.datasets.service import DatasetService


def get_dataset_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DatasetService:
    """Construct a DatasetService backed by PostgreSQL."""
    return DatasetService(SqlDatasetRepository(db), max_upload_mb=settings.max_upload_mb)
