"""TDD tests for structured chart spec validation (US-11, ADR-0008)."""

from app.charts.schemas import ChartSpec
from app.charts.service import infer_default_chart_spec, validate_chart_spec


def test_valid_bar_chart_spec_is_accepted() -> None:
    spec = ChartSpec(chart_type="bar", x="region", y="revenue", title="Revenue by Region")
    result = validate_chart_spec(
        spec,
        columns=["region", "revenue"],
        rows=[{"region": "North", "revenue": 520.0}, {"region": "South", "revenue": 645.0}],
    )
    assert result.is_valid is True
    assert result.spec == spec
    assert result.fallback_reason is None


def test_spec_with_unknown_column_is_rejected_with_fallback_reason() -> None:
    spec = ChartSpec(chart_type="bar", x="region", y="profit", title="Profit by Region")
    result = validate_chart_spec(
        spec,
        columns=["region", "revenue"],
        rows=[{"region": "North", "revenue": 520.0}],
    )
    assert result.is_valid is False
    assert result.spec is None
    assert result.fallback_reason is not None
    assert "profit" in result.fallback_reason


def test_spec_with_unknown_series_column_is_rejected() -> None:
    spec = ChartSpec(
        chart_type="line", x="order_date", y="revenue", series="missing_col", title="Trend"
    )
    result = validate_chart_spec(
        spec,
        columns=["order_date", "revenue"],
        rows=[{"order_date": "2026-01-05", "revenue": 100.0}],
    )
    assert result.is_valid is False
    assert result.fallback_reason is not None


def test_empty_rows_rejects_chart_spec() -> None:
    spec = ChartSpec(chart_type="bar", x="region", y="revenue", title="Empty")
    result = validate_chart_spec(spec, columns=["region", "revenue"], rows=[])
    assert result.is_valid is False


def test_infer_default_chart_spec_picks_bar_for_label_and_numeric() -> None:
    spec = infer_default_chart_spec(
        columns=["region", "revenue"],
        rows=[{"region": "North", "revenue": 520.0}, {"region": "South", "revenue": 645.0}],
        title="Revenue by region",
    )
    assert spec is not None
    assert spec.chart_type == "bar"
    assert spec.x == "region"
    assert spec.y == "revenue"
