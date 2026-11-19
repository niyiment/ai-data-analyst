"""Rule: enforce table and schema allowlist; block system catalogs and other schemas."""

from sqlglot import exp

from app.query.validator.types import RuleViolation, ValidationContext

_FORBIDDEN_SCHEMAS = frozenset({"pg_catalog", "information_schema", "app", "eval", "pg_temp"})


def _collect_cte_names(statement: exp.Expr) -> set[str]:
    return {cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE) if cte.alias_or_name}


class TableAllowlistRule:
    """Ensures every referenced table belongs to the dataset's allowed tables."""

    name = "table_allowlist"

    def check(self, statement: exp.Expr, context: ValidationContext) -> list[RuleViolation]:
        cte_names = _collect_cte_names(statement)
        allowed_tables = {t.lower() for t in context.allowed_tables}
        allowed_schema = context.allowed_schema.lower()
        violations: list[RuleViolation] = []

        for table in statement.find_all(exp.Table):
            if table.catalog:
                violations.append(
                    RuleViolation(
                        rule=self.name,
                        message=f"Cross-database reference '{table.catalog}' is not allowed.",
                    )
                )
                continue

            schema = table.db.lower() if table.db else ""
            name = table.name.lower()

            if schema and (schema in _FORBIDDEN_SCHEMAS or schema != allowed_schema):
                violations.append(
                    RuleViolation(
                        rule=self.name,
                        message=f"Schema '{table.db}' is not allowed.",
                    )
                )
                continue

            if not schema and name in cte_names:
                continue

            if name.startswith("pg_") or name not in allowed_tables:
                violations.append(
                    RuleViolation(
                        rule=self.name,
                        message=f"Table '{table.name}' is not in the dataset allowlist.",
                    )
                )
        return violations
