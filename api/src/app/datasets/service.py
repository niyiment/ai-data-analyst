"""Business logic service for dataset ingestion, schema review, and samples."""

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.core.errors import NotFound, ValidationRejected
from app.core.identifiers import generate_dataset_schema_name, sanitize_identifier
from app.datasets.parser import parse_spreadsheet
from app.datasets.repository import DatasetRepository
from app.datasets.samples import SAMPLE_DATASETS
from app.datasets.schemas import (
    ColumnSchema,
    ColumnUpdateRequest,
    DatasetDetail,
    DatasetListResponse,
)
from app.datasets.type_inference import ALLOWED_PG_TYPES
from app.sessions.schemas import SessionRecord


class DatasetService:
    """Orchestrates dataset uploads, sample loading, ownership checks, and column overrides."""

    def __init__(self, repo: DatasetRepository, *, max_upload_mb: int = 10) -> None:
        self._repo = repo
        self._max_upload_mb = max_upload_mb

    async def upload_file(
        self, session: SessionRecord, filename: str, content: bytes
    ) -> DatasetDetail:
        """Parse an uploaded CSV/XLSX in a worker thread and persist its schema and rows."""
        safe_display_name = Path(filename).name or "upload.csv"
        file_type, tables = await asyncio.to_thread(
            parse_spreadsheet,
            safe_display_name,
            content,
            max_upload_mb=self._max_upload_mb,
        )
        return await self._repo.create_dataset(
            session_id=session.id,
            schema_name=generate_dataset_schema_name(),
            original_filename=safe_display_name,
            file_type=file_type,
            size_bytes=len(content),
            created_at=datetime.now(UTC),
            expires_at=session.expires_at,
            tables=tables,
        )

    async def load_sample(self, session: SessionRecord, sample_name: str) -> DatasetDetail:
        """Load a built-in sample dataset into the caller's session."""
        sample = SAMPLE_DATASETS.get(sample_name)
        if sample is None:
            raise NotFound(f"Sample dataset '{sample_name}' not found.")
        filename, content = sample
        return await self.upload_file(session, filename, content)

    async def list_datasets(self, session: SessionRecord) -> DatasetListResponse:
        """List all datasets belonging to the current session."""
        items = await self._repo.list_by_session(session.id)
        return DatasetListResponse(items=items, total=len(items))

    async def get_dataset(self, session: SessionRecord, dataset_id: uuid.UUID) -> DatasetDetail:
        """Return dataset schema and preview rows, enforcing session ownership."""
        detail = await self._repo.get_detail(session.id, dataset_id)
        if detail is None:
            raise NotFound("Dataset not found.")
        return detail

    async def update_column(
        self,
        session: SessionRecord,
        dataset_id: uuid.UUID,
        column_id: uuid.UUID,
        payload: ColumnUpdateRequest,
    ) -> ColumnSchema:
        """Rename a column or override its inferred PostgreSQL type."""
        new_name = sanitize_identifier(payload.column_name) if payload.column_name else None
        if payload.pg_type is not None and payload.pg_type not in ALLOWED_PG_TYPES:
            raise ValidationRejected(
                f"Unsupported type '{payload.pg_type}'. Allowed: {sorted(ALLOWED_PG_TYPES)}"
            )
        updated = await self._repo.update_column(
            session_id=session.id,
            dataset_id=dataset_id,
            column_id=column_id,
            new_name=new_name,
            new_type=payload.pg_type,
            description=payload.description,
        )
        if updated is None:
            raise NotFound("Column not found.")
        return updated

    async def delete_dataset(self, session: SessionRecord, dataset_id: uuid.UUID) -> None:
        """Delete a single dataset and drop its schema."""
        deleted = await self._repo.delete_dataset(session.id, dataset_id)
        if not deleted:
            raise NotFound("Dataset not found.")
