"""Quality checks for golden sets and the demo schema they run against (docs/TESTING.md 9.2)."""

import importlib.util
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

from app.evaluation.golden_sets import GOLDEN_SETS
from app.evaluation.schemas import GoldenQuestion
from app.query.validator.pipeline import validate_sql
from app.query.validator.types import ValidationContext

RETAIL = GOLDEN_SETS["retail_sales"]
REQUIRED_CATEGORIES = {
    "filter",
    "aggregate",
    "group_by",
    "join",
    "date_logic",
    "ranking",
    "ambiguity",
}
MIGRATION = Path(__file__).parents[2] / "alembic" / "versions" / "0005_demo_retail_sales.py"


def _load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("demo_migration", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_retail_set_has_about_thirty_uniquely_identified_questions() -> None:
    ids = [q.id for q in RETAIL.questions]

    assert len(ids) >= 30
    assert len(ids) == len(set(ids))


def test_retail_set_covers_every_category() -> None:
    assert {q.category for q in RETAIL.questions} >= REQUIRED_CATEGORIES


def test_only_ambiguity_questions_expect_clarification() -> None:
    for q in RETAIL.questions:
        assert q.expects_clarification == (q.category == "ambiguity"), q.id


@pytest.mark.parametrize("question", RETAIL.questions, ids=lambda q: q.id)
def test_reference_sql_passes_the_production_validator(question: GoldenQuestion) -> None:
    ctx = ValidationContext(
        allowed_schema=RETAIL.demo_schema, allowed_tables=RETAIL.allowed_tables()
    )
    result = validate_sql(question.reference_sql, ctx)

    assert result.is_valid, [v.message for v in result.violations]


def test_schema_summary_matches_migration_tables_and_columns() -> None:
    migration = _load_migration()

    assert RETAIL.demo_schema == migration.DEMO_SCHEMA
    assert set(migration.DEMO_COLUMNS) == set(RETAIL.table_names)
    for table, columns in migration.DEMO_COLUMNS.items():
        assert f"Table {table} " in RETAIL.schema_summary
        for column in columns:
            assert column in RETAIL.schema_summary, f"{table}.{column}"


def test_demo_seed_data_is_internally_consistent() -> None:
    migration = _load_migration()
    sales, regions = migration.SALES_ROWS, migration.REGION_ROWS

    assert len(sales) == 40
    assert {row[2] for row in sales} <= {row[0] for row in regions}
    for row in sales:
        units, price, revenue = row[5], Decimal(row[6]), Decimal(row[7])
        assert units * price == revenue, row[0]
