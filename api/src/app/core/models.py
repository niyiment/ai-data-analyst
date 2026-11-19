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
