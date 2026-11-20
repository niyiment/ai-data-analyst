"""LLM-backed golden-question runner: generate, validate, execute, compare (US-14)."""

import time
import uuid
from dataclasses import dataclass

from app.evaluation.comparator import results_match
from app.evaluation.schemas import (
    EvalOutcome,
    GoldenQuestion,
    GoldenSet,
    QuestionEvalExecution,
)
from app.llm.port import LLMClient
from app.llm.usage import measure_usage
from app.prompts.loader import load_prompt
from app.query.executor import ExecutionResult, QueryExecutor
from app.query.pipeline_helpers import build_user_prompt, should_skip_plan
from app.query.repository import DatasetQueryContext
from app.query.schemas import QueryPlan, QueryRequest, SqlGenerationOutput
from app.query.validator.pipeline import validate_sql
from app.query.validator.types import ValidationContext

_Verdict = tuple[EvalOutcome, str | None, str | None]


@dataclass(frozen=True)
class _Generated:
    """What the model produced for one question."""

    plan: QueryPlan | None
    sql: str


class LlmEvalRunner:
    """Runs golden questions through the same plan -> SQL -> validate -> execute path."""

    def __init__(self, golden_set: GoldenSet, *, llm: LLMClient, executor: QueryExecutor) -> None:
        self._set = golden_set
        self._llm = llm
        self._executor = executor
        self._by_id = {q.id: q for q in golden_set.questions}
        self._val_ctx = ValidationContext(
            allowed_schema=golden_set.demo_schema, allowed_tables=golden_set.allowed_tables()
        )
        self._ctx = DatasetQueryContext(
            dataset_id=uuid.uuid4(),
            schema_name=golden_set.demo_schema,
            table_names=golden_set.allowed_tables(),
            schema_summary=golden_set.schema_summary,
        )

    async def execute_question(self, question_id: str) -> QuestionEvalExecution:
        """Evaluate one golden question and classify the outcome."""
        q = self._by_id[question_id]
        skip_plan = should_skip_plan(self._set.allowed_tables(), q.question)
        start = time.perf_counter()
        with measure_usage() as usage:
            outcome, sql, failure = await self._evaluate(q, skip_plan)
        return QuestionEvalExecution(
            outcome=outcome,
            generated_sql=sql,
            latency_ms=int((time.perf_counter() - start) * 1000),
            tokens_in=usage.tokens_in,
            tokens_out=usage.tokens_out,
            failure_category=failure,
            plan_skipped=skip_plan,
        )

    async def _evaluate(self, q: GoldenQuestion, skip_plan: bool) -> _Verdict:
        try:
            generated = await self._generate(q, skip_plan)
        except Exception:  # any provider failure is an eval error, not a crash
            return EvalOutcome.ERROR, None, "llm_error"

        asked = generated.plan is not None and generated.plan.needs_clarification
        if q.expects_clarification:
            if asked:
                return EvalOutcome.CORRECT, None, None
            return EvalOutcome.WRONG, generated.sql, "missed_clarification"
        if asked:
            return EvalOutcome.WRONG, None, "unexpected_clarification"
        return await self._check_sql(q, generated.sql)

    async def _generate(self, q: GoldenQuestion, skip_plan: bool) -> _Generated:
        request = QueryRequest(question=q.question)
        plan = (
            None
            if skip_plan
            else await self._llm.generate_structured(
                system_prompt=load_prompt("plan", version="v1"),
                user_prompt=build_user_prompt(self._ctx, request, [], plan=None),
                response_model=QueryPlan,
            )
        )
        if plan is not None and plan.needs_clarification:
            return _Generated(plan=plan, sql="")
        out = await self._llm.generate_structured(
            system_prompt=load_prompt("sql", version="v1"),
            user_prompt=build_user_prompt(self._ctx, request, [], plan=plan),
            response_model=SqlGenerationOutput,
        )
        return _Generated(plan=plan, sql=out.sql)

    async def _check_sql(self, q: GoldenQuestion, raw_sql: str) -> _Verdict:
        validation = validate_sql(raw_sql, self._val_ctx)
        if not validation.is_valid or not validation.normalized_sql:
            return EvalOutcome.REJECTED, raw_sql, "validator_rejected"
        sql = validation.normalized_sql
        try:
            actual = await self._run(sql)
            expected = await self._run(q.reference_sql)
        except Exception:  # timeouts and DB errors are eval errors, not crashes
            return EvalOutcome.ERROR, sql, "execution_error"
        if results_match(expected.rows, actual.rows, order_sensitive=q.order_sensitive):
            return EvalOutcome.CORRECT, sql, None
        return EvalOutcome.WRONG, sql, "wrong_result"

    async def _run(self, sql: str) -> ExecutionResult:
        return await self._executor.execute(schema_name=self._set.demo_schema, validated_sql=sql)
