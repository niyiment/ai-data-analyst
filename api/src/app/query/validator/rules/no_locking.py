"""Rule: reject row-level locking clauses (FOR UPDATE, FOR SHARE, etc.)."""

from sqlglot import exp

from app.query.validator.types import RuleViolation, ValidationContext


class NoLockingRule:
    """Rejects any SELECT containing a FOR UPDATE / FOR SHARE locking clause."""

    name = "no_locking"

    def check(self, statement: exp.Expr, context: ValidationContext) -> list[RuleViolation]:
        del context
        if list(statement.find_all(exp.Lock)):
            return [
                RuleViolation(
                    rule=self.name,
                    message="Locking clauses (FOR UPDATE / FOR SHARE) are not allowed.",
                )
            ]
        return []
