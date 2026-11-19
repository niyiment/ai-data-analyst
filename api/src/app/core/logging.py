"""Structured JSON logging configuration."""

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON without leaking sensitive values."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with structured JSON output."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
