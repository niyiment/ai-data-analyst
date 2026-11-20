"""Database repository for datasets and per-dataset schemas."""

import uuid
from datetime import datetime
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import DatasetColumnModel, DatasetModel, DatasetTableModel
from app.datasets.ddl import (
    alter_table_column,
    create_schema_and_tables,
    drop_dataset_schema,
    fetch_preview_rows,
)
from app.datasets.parser import ParsedTable
from app.datasets.schemas import ColumnSchema, DatasetDetail, DatasetSummary, TableSchema


class DatasetRepository(Protocol):
    """Repository interface for dataset metadata and dynamic schemas."""

    async def create_dataset(
        self,
        *,
        session_id: uuid.UUID,
        schema_name: str,
        original_filename: str,
        file_type: str,
        size_bytes: int,
        created_at: datetime,
        expires_at: datetime,
        tables: list[ParsedTable],
    ) -> DatasetDetail: ...

    async def list_by_session(self, session_id: uuid.UUID) -> list[DatasetSummary]: ...

    async def get_detail(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID
    ) -> DatasetDetail | None: ...

    async def update_column(
        self,
        *,
        session_id: uuid.UUID,
        dataset_id: uuid.UUID,
        column_id: uuid.UUID,
        new_name: str | None,
        new_type: str | None,
        description: str | None,
    ) -> ColumnSchema | None: ...

    async def delete_dataset(self, session_id: uuid.UUID, dataset_id: uuid.UUID) -> bool: ...


class SqlDatasetRepository:
    """PostgreSQL-backed dataset repository."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_dataset(
        self,
        *,
        session_id: uuid.UUID,
        schema_name: str,
        original_filename: str,
        file_type: str,
        size_bytes: int,
        created_at: datetime,
        expires_at: datetime,
        tables: list[ParsedTable],
    ) -> DatasetDetail:
        await create_schema_and_tables(self._db, schema_name, tables)
        dataset = DatasetModel(
            id=uuid.uuid4(),
            session_id=session_id,
            schema_name=schema_name,
            original_filename=original_filename,
            file_type=file_type,
            size_bytes=size_bytes,
            status="ready",
            created_at=created_at,
            expires_at=expires_at,
        )
        for tbl in tables:
            dataset.tables.append(_build_table_model(tbl))
        self._db.add(dataset)
        await self._db.commit()
        return await self._build_detail(dataset)

    async def list_by_session(self, session_id: uuid.UUID) -> list[DatasetSummary]:
        stmt = (
            select(DatasetModel)
            .options(selectinload(DatasetModel.tables))
            .where(DatasetModel.session_id == session_id)
            .order_by(DatasetModel.created_at.desc())
        )
        models = list((await self._db.execute(stmt)).scalars().all())
        return [
            DatasetSummary(
                id=m.id,
                original_filename=m.original_filename,
                file_type=m.file_type,
                size_bytes=m.size_bytes,
                status=m.status,
                created_at=m.created_at,
                expires_at=m.expires_at,
                table_count=len(m.tables),
            )
            for m in models
        ]

    async def get_detail(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID
    ) -> DatasetDetail | None:
        stmt = (
            select(DatasetModel)
            .options(selectinload(DatasetModel.tables).selectinload(DatasetTableModel.columns))
            .where(DatasetModel.id == dataset_id, DatasetModel.session_id == session_id)
        )
        model = (await self._db.execute(stmt)).scalar_one_or_none()
        return await self._build_detail(model) if model is not None else None

    async def update_column(
        self,
        *,
        session_id: uuid.UUID,
        dataset_id: uuid.UUID,
        column_id: uuid.UUID,
        new_name: str | None,
        new_type: str | None,
        description: str | None,
    ) -> ColumnSchema | None:
        stmt = (
            select(DatasetColumnModel, DatasetTableModel, DatasetModel)
            .join(DatasetTableModel, DatasetColumnModel.table_id == DatasetTableModel.id)
            .join(DatasetModel, DatasetTableModel.dataset_id == DatasetModel.id)
            .where(
                DatasetColumnModel.id == column_id,
                DatasetModel.id == dataset_id,
                DatasetModel.session_id == session_id,
            )
        )
        row = (await self._db.execute(stmt)).one_or_none()
        if row is None:
            return None
        col_model, tbl_model, ds_model = row
        await alter_table_column(
            self._db,
            ds_model.schema_name,
            tbl_model.table_name,
            col_model.column_name,
            new_name,
            new_type,
        )
        if new_name:
            col_model.column_name = new_name
        if new_type:
            col_model.pg_type = new_type
        if description is not None:
            col_model.description = description
        await self._db.commit()
        return _to_column_schema(col_model)

    async def delete_dataset(self, session_id: uuid.UUID, dataset_id: uuid.UUID) -> bool:
        stmt = select(DatasetModel).where(
            DatasetModel.id == dataset_id, DatasetModel.session_id == session_id
        )
        model = (await self._db.execute(stmt)).scalar_one_or_none()
        if model is None:
            return False
        await drop_dataset_schema(self._db, model.schema_name)
        await self._db.execute(delete(DatasetModel).where(DatasetModel.id == dataset_id))
        await self._db.commit()
        return True

    async def _build_detail(self, model: DatasetModel) -> DatasetDetail:
        table_schemas: list[TableSchema] = []
        for tbl in model.tables:
            preview = await fetch_preview_rows(self._db, model.schema_name, tbl.table_name)
            table_schemas.append(
                TableSchema(
                    id=tbl.id,
                    table_name=tbl.table_name,
                    source_name=tbl.source_name,
                    row_count=tbl.row_count,
                    columns=[_to_column_schema(c) for c in tbl.columns],
                    preview_rows=preview,
                )
            )
        return DatasetDetail(
            id=model.id,
            original_filename=model.original_filename,
            file_type=model.file_type,
            size_bytes=model.size_bytes,
            status=model.status,
            created_at=model.created_at,
            expires_at=model.expires_at,
            tables=table_schemas,
        )


def _build_table_model(tbl: ParsedTable) -> DatasetTableModel:
    tbl_model = DatasetTableModel(
        id=uuid.uuid4(),
        table_name=tbl.table_name,
        source_name=tbl.source_name,
        row_count=len(tbl.rows),
    )
    for col in tbl.columns:
        tbl_model.columns.append(
            DatasetColumnModel(
                id=uuid.uuid4(),
                ordinal=col.ordinal,
                original_name=col.original_name,
                column_name=col.column_name,
                pg_type=col.pg_type,
                nullable=col.nullable,
                sample_values=col.sample_values,
            )
        )
    return tbl_model


def _to_column_schema(model: DatasetColumnModel) -> ColumnSchema:
    return ColumnSchema(
        id=model.id,
        ordinal=model.ordinal,
        original_name=model.original_name,
        column_name=model.column_name,
        pg_type=model.pg_type,
        nullable=model.nullable,
        sample_values=model.sample_values,
        description=model.description,
    )
