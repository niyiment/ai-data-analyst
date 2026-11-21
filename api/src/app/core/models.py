"""SQLAlchemy ORM models for the app metadata schema (docs/DATABASE.md 6.3)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Text,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

metadata_obj = MetaData(schema="app")


class Base(DeclarativeBase):
    """Declarative base bound to the app schema."""

    metadata = metadata_obj


class SessionModel(Base):
    """Anonymous user session row."""

    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_expires_at", "expires_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    ip_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    datasets: Mapped[list["DatasetModel"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class DatasetModel(Base):
    """Uploaded or sample dataset metadata."""

    __tablename__ = "datasets"
    __table_args__ = (Index("ix_datasets_session_id", "session_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("app.sessions.id", ondelete="CASCADE"), nullable=False
    )
    schema_name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="processing")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped[SessionModel] = relationship(back_populates="datasets")
    tables: Mapped[list["DatasetTableModel"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetTableModel(Base):
    """One table per CSV file or Excel sheet."""

    __tablename__ = "dataset_tables"
    __table_args__ = (Index("ix_dataset_tables_dataset_id", "dataset_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("app.datasets.id", ondelete="CASCADE"), nullable=False
    )
    table_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    dataset: Mapped[DatasetModel] = relationship(back_populates="tables")
    columns: Mapped[list["DatasetColumnModel"]] = relationship(
        back_populates="table", cascade="all, delete-orphan", order_by="DatasetColumnModel.ordinal"
    )


class DatasetColumnModel(Base):
    """Inferred or user-overridden column metadata."""

    __tablename__ = "dataset_columns"
    __table_args__ = (Index("ix_dataset_columns_table_ordinal", "table_id", "ordinal"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("app.dataset_tables.id", ondelete="CASCADE"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    original_name: Mapped[str] = mapped_column(Text, nullable=False)
    column_name: Mapped[str] = mapped_column(Text, nullable=False)
    pg_type: Mapped[str] = mapped_column(Text, nullable=False)
    nullable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sample_values: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    table: Mapped[DatasetTableModel] = relationship(back_populates="columns")


class QueryRunModel(Base):
    """Persisted metadata for a natural-language question and its validated SQL run."""

    __tablename__ = "query_runs"
    __table_args__ = (Index("ix_query_runs_session_created", "session_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("app.sessions.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("app.datasets.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    plan: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_status: Mapped[str] = mapped_column(Text, nullable=False)
    rejection_reasons: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    truncated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stage_timings_ms: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QueryArtifactModel(Base):
    """Persisted chart_spec or insights artifact for a query run."""

    __tablename__ = "query_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    query_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("app.query_runs.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ReportModel(Base):
    """User-assembled report pinning one or more query runs."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("app.sessions.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    items: Mapped[list["ReportItemModel"]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="ReportItemModel.position"
    )


class ReportItemModel(Base):
    """Ordered item inside a report referencing a query run."""

    __tablename__ = "report_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("app.reports.id", ondelete="CASCADE"), nullable=False
    )
    query_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("app.query_runs.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    report: Mapped[ReportModel] = relationship(back_populates="items")
