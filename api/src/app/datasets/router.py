"""HTTP router for datasets (upload, samples, list, detail, column update, delete)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile

from app.datasets.dependencies import get_dataset_service
from app.datasets.schemas import (
    ColumnSchema,
    ColumnUpdateRequest,
    DatasetDetail,
    DatasetListResponse,
)
from app.datasets.service import DatasetService
from app.sessions.dependencies import require_session
from app.sessions.schemas import SessionRecord

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


@router.post("", response_model=DatasetDetail, status_code=201)
async def upload_dataset(
    file: UploadFile,
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> DatasetDetail:
    """Upload a CSV or Excel file and create its isolated PostgreSQL schema."""
    content = await file.read()
    return await service.upload_file(session, file.filename or "upload.csv", content)


@router.post("/samples/{name}", response_model=DatasetDetail, status_code=201)
async def load_sample_dataset(
    name: str,
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> DatasetDetail:
    """Load a built-in sample dataset into the current session."""
    return await service.load_sample(session, name)


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> DatasetListResponse:
    """List datasets owned by the current session."""
    return await service.list_datasets(session)


@router.get("/{dataset_id}", response_model=DatasetDetail)
async def get_dataset(
    dataset_id: uuid.UUID,
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> DatasetDetail:
    """Return a dataset's schema and preview rows."""
    return await service.get_dataset(session, dataset_id)


@router.patch("/{dataset_id}/columns/{column_id}", response_model=ColumnSchema)
async def update_column(
    dataset_id: uuid.UUID,
    column_id: uuid.UUID,
    payload: ColumnUpdateRequest,
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> ColumnSchema:
    """Rename a column or override its inferred PostgreSQL type."""
    return await service.update_column(session, dataset_id, column_id, payload)


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: uuid.UUID,
    session: Annotated[SessionRecord, Depends(require_session)],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> None:
    """Delete one dataset and drop its schema."""
    await service.delete_dataset(session, dataset_id)
