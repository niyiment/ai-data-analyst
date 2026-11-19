"""Shared PostgreSQL identifier sanitisation and schema naming."""

import re
import secrets

MAX_IDENTIFIER_LENGTH = 63
_NON_ALNUM_RE = re.compile(r"[^a-z0-9_]+")
_RESERVED_WORDS = frozenset({"select", "from", "where", "table", "user", "order", "group", "index"})


def generate_dataset_schema_name() -> str:
    """Generate a server-controlled schema name for an uploaded dataset."""
    return f"ds_{secrets.token_hex(8)}"


def sanitize_identifier(raw_name: str, fallback: str = "col") -> str:
    """Convert an arbitrary column or table name into a safe PostgreSQL identifier."""
    cleaned = _NON_ALNUM_RE.sub("_", raw_name.strip().lower()).strip("_")
    if not cleaned:
        cleaned = fallback
    if cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    if cleaned in _RESERVED_WORDS:
        cleaned = f"{cleaned}_col"
    return cleaned[:MAX_IDENTIFIER_LENGTH]
