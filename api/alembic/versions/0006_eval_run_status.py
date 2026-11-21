"""Track evaluation run status so runs can execute in the background.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "eval_runs",
        sa.Column("status", sa.Text(), nullable=False, server_default="completed"),
        schema="app",
    )
    op.add_column("eval_runs", sa.Column("error", sa.Text(), nullable=True), schema="app")
    op.alter_column("eval_runs", "finished_at", nullable=True, schema="app")


def downgrade() -> None:
    op.execute("DELETE FROM app.eval_runs WHERE finished_at IS NULL")
    op.alter_column("eval_runs", "finished_at", nullable=False, schema="app")
    op.drop_column("eval_runs", "error", schema="app")
    op.drop_column("eval_runs", "status", schema="app")
