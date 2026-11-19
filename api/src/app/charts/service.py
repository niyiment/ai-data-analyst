"""Chart specification validator and default chart recommender (US-11, ADR-0008)."""

from typing import Any

from app.charts.schemas import ChartSpec, ChartType, ChartValidationResult


def _is_numeric_column(col: str, rows: list[dict[str, Any]]) -> bool:
    non_null = [r.get(col) for r in rows if r.get(col) is not None]
    if not non_null:
        return False
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in non_null)


def validate_chart_spec(
    spec: ChartSpec,
    *,
    columns: list[str],
    rows: list[dict[str, Any]],
) -> ChartValidationResult:
    """Validate that a chart spec references only existing columns and non-empty rows."""
    if not rows:
        return ChartValidationResult(
            is_valid=False,
            fallback_reason="No rows returned; displaying table only.",
        )

    col_set = set(columns)
    for field_name, col_name in (("x", spec.x), ("y", spec.y)):
        if col_name not in col_set:
            return ChartValidationResult(
                is_valid=False,
                fallback_reason=(
                    f"Chart {field_name}-axis column '{col_name}' does not exist in results."
                ),
            )

    if spec.series and spec.series not in col_set:
        return ChartValidationResult(
            is_valid=False,
            fallback_reason=f"Chart series column '{spec.series}' does not exist in results.",
        )

    return ChartValidationResult(is_valid=True, spec=spec)


def infer_default_chart_spec(
    *,
    columns: list[str],
    rows: list[dict[str, Any]],
    title: str,
) -> ChartSpec | None:
    """Heuristically recommend a safe bar/line chart when results have label + numeric columns."""
    if len(columns) < 2 or len(rows) < 2:
        return None
    numeric_cols = [c for c in columns if _is_numeric_column(c, rows)]
    label_cols = [c for c in columns if c not in numeric_cols]
    if not numeric_cols or not label_cols:
        return None

    x_col = label_cols[0]
    y_col = numeric_cols[0]
    chart_type: ChartType = (
        "line" if "date" in x_col.lower() or "month" in x_col.lower() else "bar"
    )
    return ChartSpec(chart_type=chart_type, x=x_col, y=y_col, title=title)
