"""SQLAlchemy ORM model for persisted evaluation runs (docs/DATABASE.md)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class EvalRunModel(Base):
    """One golden-set run: summary columns for listing plus the full detail as JSON."""

    __tablename__ = "eval_runs"
    __table_args__ = (Index("ix_eval_runs_set_started", "set_name", "started_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    set_name: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="completed")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
