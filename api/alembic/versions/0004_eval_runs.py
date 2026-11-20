"""Add eval_runs table for persisted golden-set evaluation runs.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("set_name", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        schema="app",
    )
    op.create_index(
        "ix_eval_runs_set_started", "eval_runs", ["set_name", "started_at"], schema="app"
    )


def downgrade() -> None:
    op.drop_index("ix_eval_runs_set_started", table_name="eval_runs", schema="app")
    op.drop_table("eval_runs", schema="app")
