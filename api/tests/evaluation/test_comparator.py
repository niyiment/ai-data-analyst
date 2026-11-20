"""Unit tests for execution-result comparison (docs/TESTING.md 9.2)."""

from app.evaluation.comparator import results_match


def test_matches_identical_rows_different_column_order() -> None:
    expected = [{"region": "North", "revenue": 100.0}, {"region": "South", "revenue": 50.0}]
    actual = [{"revenue": 100, "region": "North"}, {"revenue": 50, "region": "South"}]
    assert results_match(expected, actual, order_sensitive=True) is True


def test_matches_unordered_rows_when_not_order_sensitive() -> None:
    expected = [{"region": "North", "revenue": 100}, {"region": "South", "revenue": 50}]
    actual = [{"region": "South", "revenue": 50}, {"region": "North", "revenue": 100}]
    assert results_match(expected, actual, order_sensitive=False) is True


def test_fails_unordered_rows_when_order_sensitive() -> None:
    expected = [{"region": "North", "revenue": 100}, {"region": "South", "revenue": 50}]
    actual = [{"region": "South", "revenue": 50}, {"region": "North", "revenue": 100}]
    assert results_match(expected, actual, order_sensitive=True) is False


def test_fails_when_row_count_or_values_differ() -> None:
    expected = [{"total": 100}]
    actual = [{"total": 99}]
    assert results_match(expected, actual, order_sensitive=False) is False
    assert results_match(expected, [], order_sensitive=False) is False
