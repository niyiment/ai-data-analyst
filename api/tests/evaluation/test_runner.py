"""Unit tests for the LLM-backed golden-question runner (US-14, docs/TESTING.md 9.2)."""

from typing import Any, TypeVar

import pytest
from pydantic import BaseModel

from app.core.errors import QueryTimeout
from app.evaluation.runner import LlmEvalRunner
from app.evaluation.schemas import EvalOutcome, GoldenQuestion, GoldenSet
from app.query.executor import ExecutionResult
from app.query.schemas import QueryPlan, SqlGenerationOutput

T = TypeVar("T", bound=BaseModel)

REFERENCE = "SELECT region, SUM(revenue) AS total FROM sales GROUP BY region"


class FakeLLM:
    """Returns a scripted plan and SQL, or raises."""

    def __init__(self, sql: str = REFERENCE, *, clarify: bool = False, fail: bool = False) -> None:
        self._sql, self._clarify, self._fail = sql, clarify, fail
        self.calls = 0

    async def generate_structured(
        self, *, system_prompt: str, user_prompt: str, response_model: type[T]
    ) -> T:
        self.calls += 1
        if self._fail:
            raise RuntimeError("provider unavailable")
        if response_model is QueryPlan:
            plan = QueryPlan(intent="i", needs_clarification=self._clarify)
            return response_model.model_validate(plan.model_dump())
        return response_model.model_validate(SqlGenerationOutput(sql=self._sql).model_dump())


class FakeExecutor:
    """Maps SQL text to rows; raises for SQL containing a marker in `raises`."""

    def __init__(
        self, rows: dict[str, list[dict[str, Any]]], raises: frozenset[str] = frozenset()
    ) -> None:
        self._rows, self._raises = rows, raises
        self.executed: list[str] = []

    async def execute(self, *, schema_name: str, validated_sql: str) -> ExecutionResult:
        self.executed.append(validated_sql)
        if any(marker in validated_sql for marker in self._raises):
            raise QueryTimeout("too slow")
        rows = next((r for k, r in self._rows.items() if k in validated_sql), [])
        cols = list(rows[0]) if rows else []
        return ExecutionResult(columns=cols, rows=rows, row_count=len(rows), truncated=False)


def _set(**question_overrides: Any) -> GoldenSet:
    question = GoldenQuestion(
        id="q1",
        question="Revenue by region?",
        reference_sql=REFERENCE,
        category="group_by",
        difficulty="easy",
    ).model_copy(update=question_overrides)
    return GoldenSet(
        name="sales",
        demo_schema="demo_sales",
        description="d",
        schema_summary="Table sales (2 rows): region (text), revenue (numeric)",
        questions=[question],
    )


ROWS = [{"region": "North", "total": 10.0}, {"region": "South", "total": 5.0}]


@pytest.mark.asyncio
async def test_matching_results_are_correct() -> None:
    llm = FakeLLM(sql="SELECT region, SUM(revenue) AS total FROM sales GROUP BY 1")
    runner = LlmEvalRunner(_set(), llm=llm, executor=FakeExecutor({"sales": ROWS}))

    result = await runner.execute_question("q1")

    assert result.outcome == EvalOutcome.CORRECT
    assert result.failure_category is None
    assert result.generated_sql is not None
    assert llm.calls == 2


@pytest.mark.asyncio
async def test_different_results_are_wrong() -> None:
    llm = FakeLLM(sql="SELECT region, COUNT(*) AS total FROM sales GROUP BY region")
    executor = FakeExecutor({"COUNT": [{"region": "North", "total": 1}], "SUM": ROWS})
    runner = LlmEvalRunner(_set(), llm=llm, executor=executor)

    result = await runner.execute_question("q1")

    assert result.outcome == EvalOutcome.WRONG
    assert result.failure_category == "wrong_result"


@pytest.mark.asyncio
async def test_unsafe_sql_is_rejected_and_never_executed() -> None:
    executor = FakeExecutor({"sales": ROWS})
    runner = LlmEvalRunner(_set(), llm=FakeLLM(sql="DELETE FROM sales"), executor=executor)

    result = await runner.execute_question("q1")

    assert result.outcome == EvalOutcome.REJECTED
    assert result.failure_category == "validator_rejected"
    assert not any("DELETE" in s.upper() for s in executor.executed)


@pytest.mark.asyncio
async def test_llm_failure_is_an_error() -> None:
    runner = LlmEvalRunner(_set(), llm=FakeLLM(fail=True), executor=FakeExecutor({}))

    result = await runner.execute_question("q1")

    assert result.outcome == EvalOutcome.ERROR
    assert result.failure_category == "llm_error"


@pytest.mark.asyncio
async def test_execution_timeout_is_an_error() -> None:
    llm = FakeLLM(sql="SELECT region FROM sales")
    executor = FakeExecutor({"sales": ROWS}, raises=frozenset({"SELECT region FROM"}))
    runner = LlmEvalRunner(_set(), llm=llm, executor=executor)

    result = await runner.execute_question("q1")

    assert result.outcome == EvalOutcome.ERROR
    assert result.failure_category == "execution_error"


@pytest.mark.asyncio
async def test_expected_clarification_counts_as_correct() -> None:
    golden = _set(expects_clarification=True, category="ambiguity")
    runner = LlmEvalRunner(golden, llm=FakeLLM(clarify=True), executor=FakeExecutor({}))

    result = await runner.execute_question("q1")

    assert result.outcome == EvalOutcome.CORRECT


@pytest.mark.asyncio
async def test_unexpected_clarification_is_wrong() -> None:
    runner = LlmEvalRunner(_set(), llm=FakeLLM(clarify=True), executor=FakeExecutor({}))

    result = await runner.execute_question("q1")

    assert result.outcome == EvalOutcome.WRONG
    assert result.failure_category == "unexpected_clarification"


@pytest.mark.asyncio
async def test_missed_clarification_is_wrong() -> None:
    golden = _set(expects_clarification=True, category="ambiguity")
    runner = LlmEvalRunner(golden, llm=FakeLLM(), executor=FakeExecutor({"sales": ROWS}))

    result = await runner.execute_question("q1")

    assert result.outcome == EvalOutcome.WRONG
    assert result.failure_category == "missed_clarification"
