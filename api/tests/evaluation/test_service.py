"""Unit tests for EvaluationService and golden sets (US-14)."""

from collections.abc import Callable
from uuid import uuid4

import pytest

from app.core.errors import NotFound
from app.evaluation.golden_sets import GOLDEN_SETS
from app.evaluation.repository import InMemoryEvalRepository
from app.evaluation.schemas import EvalOutcome, GoldenSet, QuestionEvalExecution
from app.evaluation.service import EvaluationService


class FakeEvalRunner:
    """Deterministic runner returning controlled outcomes per question."""

    def __init__(self, outcomes: dict[str, QuestionEvalExecution]) -> None:
        self._outcomes = outcomes

    async def execute_question(self, question_id: str) -> QuestionEvalExecution:
        return self._outcomes[question_id]


def _factory(
    runner: FakeEvalRunner, seen: list[str] | None = None
) -> Callable[[GoldenSet], FakeEvalRunner]:
    def build(golden_set: GoldenSet) -> FakeEvalRunner:
        if seen is not None:
            seen.append(golden_set.name)
        return runner

    return build


@pytest.mark.asyncio
async def test_list_sets_returns_retail_sales_golden_set() -> None:
    repo = InMemoryEvalRepository()
    service = EvaluationService(repo=repo, runner_factory=_factory(FakeEvalRunner({})))

    sets = service.list_sets()
    assert len(sets) >= 1
    by_name = {s.name: s for s in sets}
    assert by_name["retail_sales"].question_count >= 30
    assert by_name["retail_orders"].question_count >= 20


@pytest.mark.asyncio
async def test_run_evaluation_computes_accuracy_rejection_latency_and_tokens() -> None:
    golden_set = GOLDEN_SETS["retail_sales"]
    outcomes: dict[str, QuestionEvalExecution] = {}
    for idx, q in enumerate(golden_set.questions):
        if idx == 0:
            outcomes[q.id] = QuestionEvalExecution(
                outcome=EvalOutcome.REJECTED,
                generated_sql="DROP TABLE retail_sales",
                latency_ms=120,
                tokens_in=50,
                tokens_out=20,
                failure_category="validator_rejected",
            )
        else:
            outcomes[q.id] = QuestionEvalExecution(
                outcome=EvalOutcome.CORRECT,
                generated_sql=q.reference_sql,
                latency_ms=200 + idx * 10,
                tokens_in=100,
                tokens_out=40,
            )

    repo = InMemoryEvalRepository()
    seen: list[str] = []
    service = EvaluationService(
        repo=repo,
        runner_factory=_factory(FakeEvalRunner(outcomes), seen),
        model_name="fake:model",
    )

    run = await service.run_evaluation("retail_sales")
    total = len(golden_set.questions)
    assert run.set_name == "retail_sales"
    assert run.total_questions == total
    assert run.correct_count == total - 1
    assert run.rejected_count == 1
    assert run.accuracy == pytest.approx((total - 1) / total)
    assert run.rejection_rate == pytest.approx(1 / total)
    assert run.failure_categories == {"validator_rejected": 1}
    assert run.total_tokens_in == 50 + (total - 1) * 100
    assert run.p95_latency_ms >= run.p50_latency_ms > 0

    assert seen == ["retail_sales"]
    assert run.model == "fake:model"
    fetched = await service.get_run(run.id)
    assert fetched.id == run.id


@pytest.mark.asyncio
async def test_run_evaluation_unknown_set_raises_not_found() -> None:
    service = EvaluationService(
        repo=InMemoryEvalRepository(), runner_factory=_factory(FakeEvalRunner({}))
    )
    with pytest.raises(NotFound):
        await service.run_evaluation("does_not_exist")


@pytest.mark.asyncio
async def test_get_unknown_run_raises_not_found() -> None:
    service = EvaluationService(
        repo=InMemoryEvalRepository(), runner_factory=_factory(FakeEvalRunner({}))
    )
    with pytest.raises(NotFound):
        await service.get_run(uuid4())


@pytest.mark.asyncio
async def test_run_reports_accuracy_separately_for_planned_and_direct_paths() -> None:
    golden_set = GOLDEN_SETS["retail_sales"]
    outcomes = {
        q.id: QuestionEvalExecution(
            outcome=EvalOutcome.CORRECT if idx % 2 == 0 else EvalOutcome.WRONG,
            latency_ms=10,
            plan_skipped=idx < 4,
        )
        for idx, q in enumerate(golden_set.questions)
    }
    service = EvaluationService(
        repo=InMemoryEvalRepository(), runner_factory=_factory(FakeEvalRunner(outcomes))
    )

    run = await service.run_evaluation("retail_sales")

    direct = [o for o in outcomes.values() if o.plan_skipped]
    planned = [o for o in outcomes.values() if not o.plan_skipped]

    def acc(items: list[QuestionEvalExecution]) -> float:
        return sum(o.outcome == EvalOutcome.CORRECT for o in items) / len(items)

    assert run.accuracy_by_path == {
        "direct": pytest.approx(acc(direct)),
        "planned": pytest.approx(acc(planned)),
    }
    assert all(r.plan_skipped == outcomes[r.question_id].plan_skipped for r in run.results)
