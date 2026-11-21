"""Add query_artifacts, reports, and report_items tables (docs/DATABASE.md 6.3).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "query_artifacts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "query_run_id",
            sa.Uuid(),
            sa.ForeignKey("app.query_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.true()),
        schema="app",
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "session_id",
            sa.Uuid(),
            sa.ForeignKey("app.sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="app",
    )
    op.create_table(
        "report_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "report_id",
            sa.Uuid(),
            sa.ForeignKey("app.reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "query_run_id",
            sa.Uuid(),
            sa.ForeignKey("app.query_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        schema="app",
    )


def downgrade() -> None:
    op.drop_table("report_items", schema="app")
    op.drop_table("reports", schema="app")
    op.drop_table("query_artifacts", schema="app")
