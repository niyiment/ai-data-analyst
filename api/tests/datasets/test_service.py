"""Unit tests for DatasetService (US-04, US-05, US-06)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.errors import NotFound, ValidationRejected
from app.datasets.parser import ParsedTable
from app.datasets.schemas import (
    ColumnSchema,
    ColumnUpdateRequest,
    DatasetDetail,
    DatasetSummary,
    TableSchema,
)
from app.datasets.service import DatasetService
from app.sessions.schemas import SessionRecord


class FakeDatasetRepository:
    """In-memory DatasetRepository fake for unit tests."""

    def __init__(self) -> None:
        self.datasets: dict[uuid.UUID, tuple[uuid.UUID, DatasetDetail]] = {}

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
        ds_id = uuid.uuid4()
        table_schemas = [
            TableSchema(
                id=uuid.uuid4(),
                table_name=t.table_name,
                source_name=t.source_name,
                row_count=len(t.rows),
                columns=[
                    ColumnSchema(
                        id=uuid.uuid4(),
                        ordinal=c.ordinal,
                        original_name=c.original_name,
                        column_name=c.column_name,
                        pg_type=c.pg_type,
                        nullable=c.nullable,
                        sample_values=c.sample_values,
                    )
                    for c in t.columns
                ],
                preview_rows=[],
            )
            for t in tables
        ]
        detail = DatasetDetail(
            id=ds_id,
            original_filename=original_filename,
            file_type=file_type,
            size_bytes=size_bytes,
            status="ready",
            created_at=created_at,
            expires_at=expires_at,
            tables=table_schemas,
        )
        self.datasets[ds_id] = (session_id, detail)
        return detail

    async def list_by_session(self, session_id: uuid.UUID) -> list[DatasetSummary]:
        return [
            DatasetSummary(
                id=d.id,
                original_filename=d.original_filename,
                file_type=d.file_type,
                size_bytes=d.size_bytes,
                status=d.status,
                created_at=d.created_at,
                expires_at=d.expires_at,
                table_count=len(d.tables),
            )
            for sid, d in self.datasets.values()
            if sid == session_id
        ]

    async def get_detail(
        self, session_id: uuid.UUID, dataset_id: uuid.UUID
    ) -> DatasetDetail | None:
        entry = self.datasets.get(dataset_id)
        if entry is None or entry[0] != session_id:
            return None
        return entry[1]

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
        detail = await self.get_detail(session_id, dataset_id)
        if detail is None:
            return None
        for tbl in detail.tables:
            for idx, col in enumerate(tbl.columns):
                if col.id == column_id:
                    updated = col.model_copy(
                        update={
                            "column_name": new_name or col.column_name,
                            "pg_type": new_type or col.pg_type,
                            "description": description
                            if description is not None
                            else col.description,
                        }
                    )
                    tbl.columns[idx] = updated
                    return updated
        return None

    async def delete_dataset(self, session_id: uuid.UUID, dataset_id: uuid.UUID) -> bool:
        entry = self.datasets.get(dataset_id)
        if entry is None or entry[0] != session_id:
            return False
        del self.datasets[dataset_id]
        return True


def _make_session() -> SessionRecord:
    now = datetime.now(UTC)
    return SessionRecord(
        id=uuid.uuid4(),
        token_hash="hash",
        created_at=now,
        expires_at=now + timedelta(hours=24),
        status="active",
    )


async def test_load_sample_and_enforce_ownership() -> None:
    repo = FakeDatasetRepository()
    service = DatasetService(repo)
    owner = _make_session()
    other = _make_session()

    detail = await service.load_sample(owner, "retail_sales")
    assert detail.original_filename == "retail_sales.csv"
    assert len(detail.tables) == 1
    assert detail.tables[0].row_count == 8

    with pytest.raises(NotFound):
        await service.get_dataset(other, detail.id)


async def test_update_column_sanitizes_name_and_validates_type() -> None:
    repo = FakeDatasetRepository()
    service = DatasetService(repo)
    owner = _make_session()
    detail = await service.load_sample(owner, "retail_sales")
    col_id = detail.tables[0].columns[0].id

    updated = await service.update_column(
        owner,
        detail.id,
        col_id,
        ColumnUpdateRequest(column_name="Order Number!", pg_type="text"),
    )
    assert updated.column_name == "order_number"
    assert updated.pg_type == "text"

    with pytest.raises(ValidationRejected):
        await service.update_column(
            owner,
            detail.id,
            col_id,
            ColumnUpdateRequest(pg_type="drop table users"),
        )


async def test_unknown_sample_raises_not_found() -> None:
    service = DatasetService(FakeDatasetRepository())

    with pytest.raises(NotFound):
        await service.load_sample(_make_session(), "no_such_sample")


async def test_update_of_missing_column_raises_not_found() -> None:
    service = DatasetService(FakeDatasetRepository())
    owner = _make_session()
    detail = await service.load_sample(owner, "retail_sales")

    with pytest.raises(NotFound):
        await service.update_column(
            owner, detail.id, uuid.uuid4(), ColumnUpdateRequest(column_name="x")
        )


async def test_delete_then_get_and_delete_again_raise_not_found() -> None:
    service = DatasetService(FakeDatasetRepository())
    owner = _make_session()
    detail = await service.load_sample(owner, "retail_sales")

    await service.delete_dataset(owner, detail.id)

    with pytest.raises(NotFound):
        await service.get_dataset(owner, detail.id)
    with pytest.raises(NotFound):
        await service.delete_dataset(owner, detail.id)


async def test_list_datasets_only_returns_the_callers_datasets() -> None:
    service = DatasetService(FakeDatasetRepository())
    owner, other = _make_session(), _make_session()
    await service.load_sample(owner, "retail_sales")

    assert (await service.list_datasets(owner)).total == 1
    assert (await service.list_datasets(other)).total == 0
