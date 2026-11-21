"""Identifier sanitisation: an injection boundary for user-supplied names (DATABASE.md 6.5)."""

import re

import pytest

from app.core.identifiers import (
    MAX_IDENTIFIER_LENGTH,
    generate_dataset_schema_name,
    sanitize_identifier,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Order Number!", "order_number"),
        ("  Revenue ($)  ", "revenue"),
        ("2024 Sales", "_2024_sales"),
        ("select", "select_col"),
        ("Order", "order_col"),
        ("", "col"),
        ("!!!", "col"),
        ('x"; DROP TABLE users; --', "x_drop_table_users"),
        ("région", "r_gion"),
    ],
)
def test_sanitize_identifier(raw: str, expected: str) -> None:
    assert sanitize_identifier(raw) == expected


def test_sanitize_identifier_uses_the_given_fallback() -> None:
    assert sanitize_identifier("  ", fallback="sheet") == "sheet"


def test_sanitize_identifier_truncates_to_the_postgres_limit() -> None:
    assert len(sanitize_identifier("a" * 200)) == MAX_IDENTIFIER_LENGTH


@pytest.mark.parametrize("raw", ["a b", "A;B", "1x", "--", "Ünïcödé name", "tab\tname"])
def test_sanitized_identifiers_are_always_safe(raw: str) -> None:
    assert re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", sanitize_identifier(raw))


def test_schema_names_are_server_generated_and_unique() -> None:
    names = {generate_dataset_schema_name() for _ in range(200)}

    assert len(names) == 200
    assert all(re.fullmatch(r"ds_[0-9a-f]{16}", n) for n in names)
