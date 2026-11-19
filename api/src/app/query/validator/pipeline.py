"""AST-based SQL validation pipeline (ADR-0005)."""

import sqlglot
from sqlglot.errors import ParseError

from app.query.validator.rules.function_allowlist import FunctionAllowlistRule
from app.query.validator.rules.no_locking import NoLockingRule
from app.query.validator.rules.select_only import SelectOnlyRule
from app.query.validator.rules.table_allowlist import TableAllowlistRule
from app.query.validator.types import (
    RuleViolation,
    ValidationContext,
    ValidationResult,
    ValidatorRule,
)

DEFAULT_RULES: tuple[ValidatorRule, ...] = (
    SelectOnlyRule(),
    NoLockingRule(),
    TableAllowlistRule(),
    FunctionAllowlistRule(),
)


def _reject(rule: str, message: str) -> ValidationResult:
    return ValidationResult(is_valid=False, violations=[RuleViolation(rule=rule, message=message)])


def validate_sql(
    raw_sql: str,
    context: ValidationContext,
    rules: tuple[ValidatorRule, ...] = DEFAULT_RULES,
) -> ValidationResult:
    """Parse raw_sql with SQLGlot and run every rule; fail closed on any error."""
    cleaned = raw_sql.strip()
    if not cleaned:
        return _reject("parse", "SQL query is empty.")

    try:
        parsed = [stmt for stmt in sqlglot.parse(cleaned, read="postgres") if stmt is not None]
    except ParseError as exc:
        return _reject("parse", f"Invalid SQL syntax: {exc}")

    if len(parsed) != 1:
        return _reject("single_statement", f"Expected exactly 1 SQL statement, got {len(parsed)}.")

    statement = parsed[0]
    violations: list[RuleViolation] = []
    for rule in rules:
        violations.extend(rule.check(statement, context))

    if violations:
        return ValidationResult(is_valid=False, violations=violations)
    return ValidationResult(is_valid=True, normalized_sql=statement.sql(dialect="postgres"))
