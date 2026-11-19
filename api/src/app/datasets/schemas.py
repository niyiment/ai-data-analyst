"""Pydantic schemas for datasets, tables, columns, and previews."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    """Public metadata for a single table column."""

    id: uuid.UUID
    ordinal: int
    original_name: str
    column_name: str
    pg_type: str
    nullable: bool
    sample_values: list[Any]
    description: str | None = None


class TableSchema(BaseModel):
    """Public metadata for one table (CSV or Excel sheet)."""

    id: uuid.UUID
    table_name: str
    source_name: str
    row_count: int
    columns: list[ColumnSchema]
    preview_rows: list[dict[str, Any]] = Field(default_factory=list)


class DatasetSummary(BaseModel):
    """List-view summary of a dataset."""

    id: uuid.UUID
    original_filename: str
    file_type: str
    size_bytes: int
    status: str
    created_at: datetime
    expires_at: datetime
    table_count: int


class DatasetDetail(BaseModel):
    """Full dataset metadata including tables, columns, and preview rows."""

    id: uuid.UUID
    original_filename: str
    file_type: str
    size_bytes: int
    status: str
    created_at: datetime
    expires_at: datetime
    tables: list[TableSchema]


class DatasetListResponse(BaseModel):
    """Paginated list of datasets owned by the current session."""

    items: list[DatasetSummary]
    total: int


class ColumnUpdateRequest(BaseModel):
    """Request payload to rename a column or override its inferred PostgreSQL type."""

    column_name: str | None = None
    pg_type: str | None = None
    description: str | None = None
