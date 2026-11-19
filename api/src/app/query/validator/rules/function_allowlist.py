"""Rule: allow only safe analytical, aggregate, string, math, and date functions."""

from sqlglot import exp

from app.query.validator.types import RuleViolation, ValidationContext

ALLOWED_FUNCTIONS = frozenset(
    {
        # Aggregates & window
        "count",
        "sum",
        "avg",
        "min",
        "max",
        "stddev",
        "variance",
        "percentile_cont",
        "percentile_disc",
        "bool_and",
        "bool_or",
        "string_agg",
        "array_agg",
        "row_number",
        "rank",
        "dense_rank",
        "ntile",
        "lag",
        "lead",
        "first_value",
        "last_value",
        # Math
        "abs",
        "round",
        "ceil",
        "ceiling",
        "floor",
        "power",
        "sqrt",
        "mod",
        "ln",
        "log",
        "exp",
        "greatest",
        "least",
        "sign",
        "trunc",
        # String
        "lower",
        "upper",
        "trim",
        "ltrim",
        "rtrim",
        "length",
        "char_length",
        "substring",
        "substr",
        "left",
        "right",
        "concat",
        "concat_ws",
        "replace",
        "split_part",
        "strpos",
        "position",
        "initcap",
        "lpad",
        "rpad",
        "btrim",
        "to_char",
        # Null & conditional
        "coalesce",
        "nullif",
        # Date & time
        "date_trunc",
        "timestamp_trunc",
        "date_part",
        "extract",
        "age",
        "now",
        "current_date",
        "current_timestamp",
        "to_date",
        "to_timestamp",
        "make_date",
        # Casting / type helpers
        "cast",
    }
)


class FunctionAllowlistRule:
    """Rejects any SQL function not in the explicit analytical allowlist."""

    name = "function_allowlist"

    def check(self, statement: exp.Expr, context: ValidationContext) -> list[RuleViolation]:
        del context
        violations: list[RuleViolation] = []
        for func in statement.find_all(exp.Func):
            name = (func.sql_name() or "").lower()
            if not name:
                continue
            if name.startswith("pg_") or name not in ALLOWED_FUNCTIONS:
                violations.append(
                    RuleViolation(
                        rule=self.name,
                        message=f"Function '{name}' is not in the safe function allowlist.",
                    )
                )
        return violations
