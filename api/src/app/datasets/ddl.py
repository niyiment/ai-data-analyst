"""Dynamic PostgreSQL DDL and row-loading helpers using psycopg.sql.Identifier."""

from typing import Any

from psycopg import sql
from sqlalchemy.ext.asyncio import AsyncSession

from app.datasets.parser import ParsedTable

PREVIEW_ROW_LIMIT = 10


async def _raw_cursor(db: AsyncSession) -> Any:
    raw_conn = await db.connection()
    driver_conn = await raw_conn.get_raw_connection()
    return driver_conn.driver_connection.cursor()  # type: ignore[union-attr]


async def create_schema_and_tables(
    db: AsyncSession, schema_name: str, tables: list[ParsedTable]
) -> None:
    """Create a per-dataset schema, grant read-only access to analyst_ro, and load rows."""
    async with await _raw_cursor(db) as cur:
        await cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
        await cur.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO analyst_ro").format(sql.Identifier(schema_name))
        )
        for table in tables:
            await _create_and_populate_table(cur, schema_name, table)
        await cur.execute(
            sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO analyst_ro").format(
                sql.Identifier(schema_name)
            )
        )


async def _create_and_populate_table(cur: Any, schema_name: str, table: ParsedTable) -> None:
    col_defs = sql.SQL(", ").join(
        sql.SQL("{} {}").format(sql.Identifier(col.column_name), sql.SQL(col.pg_type))
        for col in table.columns
    )
    await cur.execute(
        sql.SQL("CREATE TABLE {}.{} ({})").format(
            sql.Identifier(schema_name), sql.Identifier(table.table_name), col_defs
        )
    )
    if not table.rows:
        return
    col_idents = sql.SQL(", ").join(sql.Identifier(c.column_name) for c in table.columns)
    placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in table.columns)
    insert_stmt = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(schema_name),
        sql.Identifier(table.table_name),
        col_idents,
        placeholders,
    )
    await cur.executemany(insert_stmt, table.rows)


async def fetch_preview_rows(
    db: AsyncSession, schema_name: str, table_name: str, limit: int = PREVIEW_ROW_LIMIT
) -> list[dict[str, Any]]:
    """Fetch the first N rows of a dataset table as JSON-serialisable dicts."""
    stmt = sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(
        sql.Identifier(schema_name), sql.Identifier(table_name)
    )
    async with await _raw_cursor(db) as cur:
        await cur.execute(stmt, (limit,))
        col_names = [desc[0] for desc in (cur.description or [])]
        rows = await cur.fetchall()
    return [
        {name: _serialize_cell(val) for name, val in zip(col_names, row, strict=True)}
        for row in rows
    ]


async def alter_table_column(
    db: AsyncSession,
    schema_name: str,
    table_name: str,
    old_name: str,
    new_name: str | None,
    new_type: str | None,
) -> None:
    """Rename a column and/or cast its PostgreSQL type in-place."""
    current_name = old_name
    async with await _raw_cursor(db) as cur:
        if new_name and new_name != old_name:
            await cur.execute(
                sql.SQL("ALTER TABLE {}.{} RENAME COLUMN {} TO {}").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name),
                    sql.Identifier(old_name),
                    sql.Identifier(new_name),
                )
            )
            current_name = new_name
        if new_type:
            await cur.execute(
                sql.SQL("ALTER TABLE {}.{} ALTER COLUMN {} TYPE {t} USING {}::{t}").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name),
                    sql.Identifier(current_name),
                    sql.Identifier(current_name),
                    t=sql.SQL(new_type),
                )
            )


async def drop_dataset_schema(db: AsyncSession, schema_name: str) -> None:
    """Drop a dataset's PostgreSQL schema idempotently."""
    async with await _raw_cursor(db) as cur:
        await cur.execute(
            sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
        )


def _serialize_cell(val: Any) -> Any:
    if val is None or isinstance(val, (str, int, float, bool)):
        return val
    return str(val)
