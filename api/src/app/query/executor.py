"""Read-only PostgreSQL query executor using the analyst_ro role (ADR-0005)."""

from dataclasses import dataclass
from typing import Any, Protocol

import psycopg
from psycopg import sql
from psycopg.errors import QueryCanceled

from app.core.errors import QueryTimeout


@dataclass(frozen=True)
class ExecutionResult:
    """Result rows returned by the read-only executor."""

    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool


class QueryExecutor(Protocol):
    """Abstract interface for executing validated read-only SQL."""

    async def execute(self, *, schema_name: str, validated_sql: str) -> ExecutionResult: ...


class PostgresReadOnlyExecutor:
    """Executes validated SQL on analyst_ro inside a read-only transaction with timeout and cap."""

    def __init__(
        self,
        analyst_dsn: str,
        *,
        timeout_seconds: int = 10,
        max_rows: int = 500,
    ) -> None:
        self._dsn = analyst_dsn.replace("postgresql+psycopg://", "postgresql://")
        self._timeout_ms = timeout_seconds * 1000
        self._max_rows = max_rows

    async def execute(self, *, schema_name: str, validated_sql: str) -> ExecutionResult:
        wrapped = f"SELECT * FROM ({validated_sql}) AS _ada_sub LIMIT {self._max_rows + 1}"
        async with (
            await psycopg.AsyncConnection.connect(self._dsn) as conn,
            conn.transaction(),
            conn.cursor() as cur,
        ):
            await cur.execute("SET TRANSACTION READ ONLY")
            await cur.execute(
                sql.SQL("SET LOCAL statement_timeout = {}").format(sql.Literal(self._timeout_ms))
            )
            await cur.execute(
                sql.SQL("SET LOCAL search_path = {}").format(sql.Identifier(schema_name))
            )
            try:
                await cur.execute(wrapped)
            except QueryCanceled as exc:
                raise QueryTimeout(
                    "Query exceeded the time limit. Try narrowing your question."
                ) from exc
            col_names = [desc[0] for desc in (cur.description or [])]
            raw_rows = await cur.fetchall()

        truncated = len(raw_rows) > self._max_rows
        sliced = raw_rows[: self._max_rows]
        rows = [
            {name: _serialize(val) for name, val in zip(col_names, row, strict=True)}
            for row in sliced
        ]
        return ExecutionResult(
            columns=col_names,
            rows=rows,
            row_count=len(rows),
            truncated=truncated,
        )


def _serialize(val: Any) -> Any:
    if val is None or isinstance(val, (str, int, float, bool)):
        return val
    return str(val)
