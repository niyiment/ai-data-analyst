"""Business logic service for the two-stage NL-to-SQL pipeline (US-07..US-10)."""

import time
import uuid
from datetime import UTC, datetime

from app.core.errors import NotFound
from app.llm.port import LLMClient
from app.prompts.loader import load_prompt
from app.query.executor import QueryExecutor
from app.query.pipeline_helpers import (
    RunMeta,
    build_user_prompt,
    make_run_and_response,
    should_skip_plan,
)
from app.query.repository import DatasetQueryContext, QueryRepository
from app.query.schemas import (
    QueryHistoryResponse,
    QueryPlan,
    QueryRequest,
    QueryResponse,
    SqlGenerationOutput,
)
from app.query.validator.pipeline import validate_sql
from app.query.validator.types import ValidationContext
from app.sessions.schemas import SessionRecord


def _ms_since(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


class QueryService:
    """Orchestrates plan -> SQL -> AST validate -> read-only execute."""

    def __init__(self, repo: QueryRepository, llm: LLMClient, executor: QueryExecutor) -> None:
        self._repo = repo
        self._llm = llm
        self._executor = executor

    async def ask(
        self, session: SessionRecord, dataset_id: uuid.UUID, request: QueryRequest
    ) -> QueryResponse:
        """Run the full safe query pipeline for a natural-language question."""
        ctx = await self._repo.get_dataset_context(session.id, dataset_id)
        if ctx is None:
            raise NotFound("Dataset not found.")

        recent = await self._repo.get_recent_questions(session.id, dataset_id, limit=3)
        timings: dict[str, int] = {}
        plan = (
            None
            if should_skip_plan(ctx.table_names, request.question)
            else await self._run_plan_stage(ctx, request, recent, timings)
        )
        meta = RunMeta(
            run_id=uuid.uuid4(),
            session_id=session.id,
            dataset_id=dataset_id,
            question=request.question,
            plan=plan,
            timings=timings,
            created_at=datetime.now(UTC),
        )

        if plan is not None and plan.needs_clarification and not request.clarification_choice:
            run, resp = make_run_and_response(
                meta,
                status="needs_clarification",
                validation_status="skipped",
                error_code="NEEDS_CLARIFICATION",
            )
            await self._repo.save_run(run)
            return resp

        sql_out = await self._run_sql_stage(ctx, request, plan, recent, timings)
        return await self._validate_and_execute(meta, ctx, sql_out.sql)

    async def list_history(
        self, session: SessionRecord, dataset_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> QueryHistoryResponse:
        """Return paginated question history for a dataset."""
        ctx = await self._repo.get_dataset_context(session.id, dataset_id)
        if ctx is None:
            raise NotFound("Dataset not found.")
        items, total = await self._repo.list_history(
            session.id, dataset_id, limit=limit, offset=offset
        )
        return QueryHistoryResponse(items=items, total=total)

    async def _run_plan_stage(
        self,
        ctx: DatasetQueryContext,
        request: QueryRequest,
        recent: list[tuple[str, dict[str, object] | None]],
        timings: dict[str, int],
    ) -> QueryPlan | None:
        start = time.perf_counter()
        plan = await self._llm.generate_structured(
            system_prompt=load_prompt("plan", version="v1"),
            user_prompt=build_user_prompt(ctx, request, recent, plan=None),
            response_model=QueryPlan,
        )
        timings["plan"] = _ms_since(start)
        return plan

    async def _run_sql_stage(
        self,
        ctx: DatasetQueryContext,
        request: QueryRequest,
        plan: QueryPlan | None,
        recent: list[tuple[str, dict[str, object] | None]],
        timings: dict[str, int],
    ) -> SqlGenerationOutput:
        start = time.perf_counter()
        output = await self._llm.generate_structured(
            system_prompt=load_prompt("sql", version="v1"),
            user_prompt=build_user_prompt(ctx, request, recent, plan=plan),
            response_model=SqlGenerationOutput,
        )
        timings["generate"] = _ms_since(start)
        return output

    async def _validate_and_execute(
        self, meta: RunMeta, ctx: DatasetQueryContext, raw_sql: str
    ) -> QueryResponse:
        val_start = time.perf_counter()
        val_ctx = ValidationContext(allowed_schema=ctx.schema_name, allowed_tables=ctx.table_names)
        validation = validate_sql(raw_sql, val_ctx)
        meta.timings["validate"] = _ms_since(val_start)

        if not validation.is_valid or not validation.normalized_sql:
            reasons = [{"rule": v.rule, "message": v.message} for v in validation.violations]
            run, resp = make_run_and_response(
                meta,
                status="rejected",
                validation_status="rejected",
                generated_sql=raw_sql,
                error_code="QUERY_REJECTED",
                rejection_reasons=reasons,
            )
            await self._repo.save_run(run)
            return resp

        exec_start = time.perf_counter()
        result = await self._executor.execute(
            schema_name=ctx.schema_name, validated_sql=validation.normalized_sql
        )
        meta.timings["execute"] = _ms_since(exec_start)
        run, resp = make_run_and_response(
            meta,
            status="succeeded",
            validation_status="accepted",
            generated_sql=validation.normalized_sql,
            exec_result=result,
        )
        await self._repo.save_run(run)
        return resp
