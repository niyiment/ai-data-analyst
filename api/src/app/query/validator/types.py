"""Types and rule interface for the AST-based SQL validator."""

from dataclasses import dataclass, field
from typing import Protocol

from sqlglot import exp


@dataclass(frozen=True)
class ValidationContext:
    """Dataset-scoped allowlist context passed to every validator rule."""

    allowed_schema: str
    allowed_tables: frozenset[str]


@dataclass(frozen=True)
class RuleViolation:
    """A single validation failure reported by a rule."""

    rule: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of running the SQL validator pipeline."""

    is_valid: bool
    normalized_sql: str | None = None
    violations: list[RuleViolation] = field(default_factory=list)


class ValidatorRule(Protocol):
    """Single-purpose SQL validation rule interface."""

    name: str

    def check(self, statement: exp.Expr, context: ValidationContext) -> list[RuleViolation]:
        """Inspect a parsed AST statement and return any violations."""
        ...
