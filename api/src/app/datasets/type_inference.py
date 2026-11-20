"""Column type inference and value casting (docs/DATABASE.md 6.6)."""

from datetime import date, datetime
from typing import Any

ALLOWED_PG_TYPES = frozenset({"boolean", "bigint", "double precision", "date", "timestamp", "text"})
NULL_MARKERS = frozenset({"", "na", "n/a", "null", "none"})
_TRUE_VALUES = frozenset({"true", "yes", "1", "t", "y"})
_FALSE_VALUES = frozenset({"false", "no", "0", "f", "n"})


def is_null_marker(value: Any) -> bool:
    """Return True if a raw cell value should be treated as SQL NULL."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in NULL_MARKERS
    return False


def _is_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return value.strip().lower() in (_TRUE_VALUES | _FALSE_VALUES)
    return False


def _is_bigint(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        try:
            int(text)
            return True
        except ValueError:
            return False
    return False


def _is_double(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        try:
            float(text)
            return True
        except ValueError:
            return False
    return False


def _is_date(value: Any) -> bool:
    if isinstance(value, date) and not isinstance(value, datetime):
        return True
    if isinstance(value, str):
        try:
            date.fromisoformat(value.strip())
            return True
        except ValueError:
            return False
    return False


def _is_timestamp(value: Any) -> bool:
    if isinstance(value, datetime):
        return True
    if isinstance(value, str):
        text = value.strip().replace("Z", "+00:00")
        try:
            datetime.fromisoformat(text)
            return True
        except ValueError:
            return False
    return False


def infer_column_type(values: list[Any], sample_size: int = 500) -> tuple[str, bool]:
    """Return (pg_type, nullable) for a column's raw values."""
    sample = values[:sample_size]
    non_null = [v for v in sample if not is_null_marker(v)]
    nullable = len(non_null) < len(sample) or not sample
    if not non_null:
        return "text", True

    checks = (
        ("boolean", _is_bool),
        ("bigint", _is_bigint),
        ("double precision", _is_double),
        ("date", _is_date),
        ("timestamp", _is_timestamp),
    )
    for pg_type, predicate in checks:
        if all(predicate(v) for v in non_null):
            return pg_type, nullable
    return "text", nullable


def cast_value(value: Any, pg_type: str) -> Any:
    """Cast a raw cell value to a Python object compatible with pg_type."""
    if is_null_marker(value):
        return None
    if pg_type == "boolean":
        return value if isinstance(value, bool) else str(value).strip().lower() in _TRUE_VALUES
    if pg_type == "bigint":
        return value if isinstance(value, int) else int(str(value).strip().replace(",", ""))
    if pg_type == "double precision":
        return (
            float(value)
            if isinstance(value, (int, float))
            else float(str(value).strip().replace(",", ""))
        )
    if pg_type == "date":
        return value if isinstance(value, date) else date.fromisoformat(str(value).strip())
    if pg_type == "timestamp":
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    return str(value)
