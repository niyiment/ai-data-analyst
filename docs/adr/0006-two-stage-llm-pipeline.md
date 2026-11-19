# ADR-0006: Two-stage LLM pipeline (plan, then SQL)

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

One-shot NL-to-SQL is brittle on ambiguous questions.

## Decision

Stage one produces a structured plan (intent, tables, columns, aggregations, filters, ambiguities). Stage two turns the plan into SQL. Ambiguity returns a clarifying question.

## Consequences

Better accuracy and explainability, at roughly twice the model calls per question. The plan stage is skipped for simple single-table questions, and evaluation tracks both paths.
