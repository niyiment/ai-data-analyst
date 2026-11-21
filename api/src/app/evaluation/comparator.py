"""Execution-result comparison for NL-to-SQL evaluation (docs/TESTING.md 9.2)."""

from typing import Any


def _normalize_value(value: Any) -> Any:
    """Normalize numeric and string values for fair SQL result comparison."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    return value


def _normalize_row(row: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    """Normalize a result row into a column-order-independent sorted tuple."""
    return tuple(sorted((k.lower(), _normalize_value(v)) for k, v in row.items()))


def results_match(
    expected: list[dict[str, Any]],
    actual: list[dict[str, Any]],
    *,
    order_sensitive: bool = False,
) -> bool:
    """Compare two SQL result sets ignoring column order and optionally row order."""
    if len(expected) != len(actual):
        return False

    norm_expected = [_normalize_row(r) for r in expected]
    norm_actual = [_normalize_row(r) for r in actual]

    if order_sensitive:
        return norm_expected == norm_actual
    return sorted(norm_expected, key=repr) == sorted(norm_actual, key=repr)
