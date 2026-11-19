"""Unit tests for column type inference (docs/DATABASE.md 6.6)."""

import pytest

from app.datasets.type_inference import cast_value, infer_column_type


@pytest.mark.parametrize(
    ("values", "expected_type", "expected_nullable"),
    [
        (["true", "false", "yes"], "boolean", False),
        (["1", "2", "3", "NA"], "bigint", True),
        (["1.5", "2", "3.14"], "double precision", False),
        (["2026-01-01", "2026-02-15"], "date", False),
        (["2026-01-01T10:30:00Z", "2026-02-15T12:00:00Z"], "timestamp", False),
        (["1", "abc", "3"], "text", False),
        (["", "N/A", "null"], "text", True),
    ],
)
def test_infer_column_type(values: list[str], expected_type: str, expected_nullable: bool) -> None:
    pg_type, nullable = infer_column_type(values)
    assert pg_type == expected_type
    assert nullable is expected_nullable


def test_cast_value_handles_null_markers_and_types() -> None:
    assert cast_value("N/A", "bigint") is None
    assert cast_value("1,234", "bigint") == 1234
    assert cast_value("3.5", "double precision") == 3.5
    assert cast_value("yes", "boolean") is True
