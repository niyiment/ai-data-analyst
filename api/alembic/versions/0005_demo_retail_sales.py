"""Create the persistent demo_retail_sales schema used by the evaluation golden set.

The seed data below is frozen: golden reference SQL depends on it, so change it
only through a new migration.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-20
"""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEMO_SCHEMA = "demo_retail_sales"
DEMO_COLUMNS: dict[str, list[str]] = {
    "retail_sales": [
        "order_id", "order_date", "region", "category", "product",
        "units", "unit_price", "revenue", "returned",
    ],
    "regions": ["region", "manager", "revenue_target"],
}  # fmt: skip

REGION_ROWS = [
    ("North", "Dana Okafor", "3000.00"),
    ("South", "Lee Park", "2500.00"),
    ("East", "Sam Rivera", "1500.00"),
    ("West", "Ari Novak", "3000.00"),
]

SALES_ROWS = [
    (1001, "2026-01-05", "North", "Furniture", "Standing Desk", 1, "420.00", "420.00", False),
    (1002, "2026-01-06", "North", "Office Supplies", "Desk Lamp", 2, "35.00", "70.00", False),
    (1003, "2026-01-09", "West", "Electronics", "Monitor Stand", 1, "65.00", "65.00", True),
    (1004, "2026-01-10", "North", "Electronics", "Monitor Stand", 2, "65.00", "130.00", False),
    (1005, "2026-01-13", "North", "Electronics", "USB-C Hub", 4, "40.00", "160.00", False),
    (1006, "2026-01-16", "South", "Office Supplies", "Pen Set", 7, "8.00", "56.00", True),
    (1007, "2026-01-17", "South", "Office Supplies", "Desk Lamp", 3, "35.00", "105.00", False),
    (1008, "2026-01-20", "South", "Electronics", "USB-C Hub", 10, "40.00", "400.00", False),
    (1009, "2026-01-21", "East", "Office Supplies", "Pen Set", 10, "8.00", "80.00", False),
    (1010, "2026-01-22", "South", "Office Supplies", "Desk Lamp", 2, "35.00", "70.00", False),
    (1011, "2026-01-24", "West", "Office Supplies", "Desk Lamp", 7, "35.00", "245.00", False),
    (1012, "2026-01-27", "South", "Office Supplies", "Notebook Pack", 6, "12.50", "75.00", False),
    (1013, "2026-01-30", "West", "Electronics", "Monitor Stand", 2, "65.00", "130.00", False),
    (1014, "2026-02-01", "North", "Office Supplies", "Notebook Pack", 5, "12.50", "62.50", False),
    (1015, "2026-02-02", "East", "Office Supplies", "Desk Lamp", 7, "35.00", "245.00", False),
    (1016, "2026-02-03", "North", "Office Supplies", "Notebook Pack", 7, "12.50", "87.50", True),
    (1017, "2026-02-06", "East", "Office Supplies", "Pen Set", 6, "8.00", "48.00", False),
    (1018, "2026-02-09", "North", "Office Supplies", "Notebook Pack", 10, "12.50", "125.00", False),
    (1019, "2026-02-10", "North", "Furniture", "Desk Chair", 2, "180.00", "360.00", False),
    (1020, "2026-02-11", "West", "Furniture", "Desk Chair", 3, "180.00", "540.00", False),
    (1021, "2026-02-13", "West", "Furniture", "Bookshelf", 3, "150.00", "450.00", False),
    (
        1022,
        "2026-02-15",
        "North",
        "Electronics",
        "Mechanical Keyboard",
        10,
        "95.00",
        "950.00",
        True,
    ),
    (1023, "2026-02-16", "West", "Furniture", "Desk Chair", 1, "180.00", "180.00", False),
    (1024, "2026-02-18", "West", "Office Supplies", "Notebook Pack", 2, "12.50", "25.00", False),
    (1025, "2026-02-21", "East", "Furniture", "Desk Chair", 1, "180.00", "180.00", False),
    (1026, "2026-02-24", "West", "Furniture", "Bookshelf", 2, "150.00", "300.00", False),
    (
        1027,
        "2026-02-25",
        "South",
        "Electronics",
        "Mechanical Keyboard",
        2,
        "95.00",
        "190.00",
        False,
    ),
    (1028, "2026-02-28", "South", "Electronics", "Monitor Stand", 1, "65.00", "65.00", False),
    (1029, "2026-03-02", "East", "Furniture", "Desk Chair", 1, "180.00", "180.00", True),
    (1030, "2026-03-05", "North", "Office Supplies", "Pen Set", 6, "8.00", "48.00", False),
    (1031, "2026-03-07", "West", "Office Supplies", "Desk Lamp", 7, "35.00", "245.00", False),
    (1032, "2026-03-08", "North", "Office Supplies", "Notebook Pack", 7, "12.50", "87.50", True),
    (1033, "2026-03-09", "North", "Office Supplies", "Notebook Pack", 3, "12.50", "37.50", True),
    (1034, "2026-03-10", "North", "Electronics", "Wireless Mouse", 10, "25.00", "250.00", False),
    (1035, "2026-03-12", "South", "Office Supplies", "Pen Set", 1, "8.00", "8.00", True),
    (1036, "2026-03-15", "East", "Furniture", "Bookshelf", 1, "150.00", "150.00", False),
    (1037, "2026-03-18", "West", "Furniture", "Standing Desk", 2, "420.00", "840.00", True),
    (1038, "2026-03-20", "South", "Office Supplies", "Notebook Pack", 8, "12.50", "100.00", False),
    (1039, "2026-03-21", "South", "Furniture", "Standing Desk", 3, "420.00", "1260.00", False),
    (1040, "2026-03-24", "East", "Electronics", "Wireless Mouse", 4, "25.00", "100.00", False),
]


def _create_tables() -> tuple[sa.Table, sa.Table]:
    regions = op.create_table(
        "regions",
        sa.Column("region", sa.Text(), primary_key=True),
        sa.Column("manager", sa.Text(), nullable=False),
        sa.Column("revenue_target", sa.Numeric(12, 2), nullable=False),
        schema=DEMO_SCHEMA,
    )
    sales = op.create_table(
        "retail_sales",
        sa.Column("order_id", sa.Integer(), primary_key=True),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("region", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("product", sa.Text(), nullable=False),
        sa.Column("units", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("revenue", sa.Numeric(12, 2), nullable=False),
        sa.Column("returned", sa.Boolean(), nullable=False),
        schema=DEMO_SCHEMA,
    )
    assert regions is not None and sales is not None
    return regions, sales


def _region_record(row: tuple[str, str, str]) -> dict[str, object]:
    region, manager, target = row
    values = (region, manager, Decimal(target))
    return dict(zip(DEMO_COLUMNS["regions"], values, strict=True))


def _sales_record(row: tuple[int, str, str, str, str, int, str, str, bool]) -> dict[str, object]:
    oid, day, region, category, product, units, price, revenue, returned = row
    values = (
        oid, date.fromisoformat(day), region, category, product,
        units, Decimal(price), Decimal(revenue), returned,
    )  # fmt: skip
    return dict(zip(DEMO_COLUMNS["retail_sales"], values, strict=True))


def _seed(regions: sa.Table, sales: sa.Table) -> None:
    op.bulk_insert(regions, [_region_record(row) for row in REGION_ROWS])
    op.bulk_insert(sales, [_sales_record(row) for row in SALES_ROWS])


def upgrade() -> None:
    op.execute(sa.schema.CreateSchema(DEMO_SCHEMA))
    regions, sales = _create_tables()
    _seed(regions, sales)
    op.execute("GRANT USAGE ON SCHEMA demo_retail_sales TO analyst_ro")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA demo_retail_sales TO analyst_ro")


def downgrade() -> None:
    op.execute(sa.schema.DropSchema(DEMO_SCHEMA, cascade=True))
