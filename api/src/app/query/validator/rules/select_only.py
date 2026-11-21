"""Rule: reject any non-SELECT statement, CTE-wrapped mutation, or SELECT INTO."""

from sqlglot import exp

from app.query.validator.types import RuleViolation, ValidationContext

_FORBIDDEN_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.Grant,
    exp.Revoke,
    exp.Command,
    exp.Copy,
    exp.Set,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
    exp.TruncateTable,
    exp.Into,
)

_ALLOWED_ROOTS = (exp.Select, exp.Union, exp.Subquery)


class SelectOnlyRule:
    """Ensures the query is strictly read-only SELECT (including CTEs and UNIONs)."""

    name = "select_only"

    def check(self, statement: exp.Expr, context: ValidationContext) -> list[RuleViolation]:
        del context
        violations: list[RuleViolation] = []
        if not isinstance(statement, _ALLOWED_ROOTS):
            violations.append(
                RuleViolation(
                    rule=self.name,
                    message=f"Only SELECT statements are allowed; got {type(statement).__name__}.",
                )
            )
            return violations

        for node in statement.walk():
            if isinstance(node, _FORBIDDEN_NODES):
                violations.append(
                    RuleViolation(
                        rule=self.name,
                        message=f"Forbidden SQL construct: {type(node).__name__}.",
                    )
                )
        return violations
