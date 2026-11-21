"""Initial metadata tables for sessions and datasets.

Revision ID: 0001
Revises:
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS app")

    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("ip_hash", sa.Text(), nullable=True),
        schema="app",
    )
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"], schema="app")

    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "session_id",
            sa.Uuid(),
            sa.ForeignKey("app.sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("schema_name", sa.Text(), nullable=False, unique=True),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("file_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="processing"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        schema="app",
    )
    op.create_index("ix_datasets_session_id", "datasets", ["session_id"], schema="app")

    op.create_table(
        "dataset_tables",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "dataset_id",
            sa.Uuid(),
            sa.ForeignKey("app.datasets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("table_name", sa.Text(), nullable=False),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        schema="app",
    )
    op.create_index("ix_dataset_tables_dataset_id", "dataset_tables", ["dataset_id"], schema="app")

    op.create_table(
        "dataset_columns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "table_id",
            sa.Uuid(),
            sa.ForeignKey("app.dataset_tables.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("original_name", sa.Text(), nullable=False),
        sa.Column("column_name", sa.Text(), nullable=False),
        sa.Column("pg_type", sa.Text(), nullable=False),
        sa.Column("nullable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sample_values", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        schema="app",
    )
    op.create_index(
        "ix_dataset_columns_table_ordinal",
        "dataset_columns",
        ["table_id", "ordinal"],
        schema="app",
    )


def downgrade() -> None:
    op.drop_table("dataset_columns", schema="app")
    op.drop_table("dataset_tables", schema="app")
    op.drop_table("datasets", schema="app")
    op.drop_table("sessions", schema="app")
