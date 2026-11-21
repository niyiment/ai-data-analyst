"""Query responses carry a validated chart recommendation (US-11, ADR-0008)."""

import uuid
from datetime import UTC, datetime
from typing import Any

from app.query.executor import ExecutionResult
from app.query.pipeline_helpers import RunMeta, make_run_and_response


def _meta() -> RunMeta:
    return RunMeta(
        run_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        dataset_id=uuid.uuid4(),
        question="Revenue by region",
        plan=None,
        timings={},
        created_at=datetime.now(UTC),
    )


def _result(rows: list[dict[str, Any]]) -> ExecutionResult:
    cols = list(rows[0]) if rows else []
    return ExecutionResult(columns=cols, rows=rows, row_count=len(rows), truncated=False)


def test_label_and_numeric_results_get_a_bar_chart_titled_by_the_question() -> None:
    rows = [{"region": "North", "total": 10.0}, {"region": "South", "total": 5.0}]

    _, resp = make_run_and_response(
        _meta(), status="succeeded", validation_status="accepted", exec_result=_result(rows)
    )

    assert resp.chart_spec is not None
    assert (resp.chart_spec.chart_type, resp.chart_spec.x, resp.chart_spec.y) == (
        "bar",
        "region",
        "total",
    )
    assert resp.chart_spec.title == "Revenue by region"


def test_single_value_results_have_no_chart() -> None:
    _, resp = make_run_and_response(
        _meta(),
        status="succeeded",
        validation_status="accepted",
        exec_result=_result([{"total_orders": 40}]),
    )

    assert resp.chart_spec is None


def test_rejected_runs_have_no_chart() -> None:
    _, resp = make_run_and_response(_meta(), status="rejected", validation_status="rejected")

    assert resp.chart_spec is None
