"""Unit tests for EvaluationService and golden sets (US-14)."""

import pytest

from app.core.errors import NotFound
from app.evaluation.golden_sets import GOLDEN_SETS
from app.evaluation.repository import InMemoryEvalRepository
from app.evaluation.schemas import EvalOutcome, QuestionEvalExecution
from app.evaluation.service import EvaluationService


class FakeEvalRunner:
    """Deterministic runner returning controlled outcomes per question."""

    def __init__(self, outcomes: dict[str, QuestionEvalExecution]) -> None:
        self._outcomes = outcomes

    async def execute_question(self, question_id: str) -> QuestionEvalExecution:
        return self._outcomes[question_id]


@pytest.mark.asyncio
async def test_list_sets_returns_retail_sales_golden_set() -> None:
    repo = InMemoryEvalRepository()
    service = EvaluationService(repo=repo)

    sets = service.list_sets()
    assert len(sets) >= 1
    assert sets[0].name == "retail_sales"
    assert sets[0].question_count >= 5


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
    service = EvaluationService(repo=repo, runner=FakeEvalRunner(outcomes))

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

    fetched = service.get_run(run.id)
    assert fetched.id == run.id


@pytest.mark.asyncio
async def test_run_evaluation_unknown_set_raises_not_found() -> None:
    service = EvaluationService(repo=InMemoryEvalRepository())
    with pytest.raises(NotFound):
        await service.run_evaluation("does_not_exist")
