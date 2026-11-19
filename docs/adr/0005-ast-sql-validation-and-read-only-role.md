# ADR-0005: AST-based SQL validation with SQLGlot plus a read-only database role

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

LLM-generated SQL is untrusted input.

## Decision

Parse with SQLGlot and validate with a pipeline of single-purpose rules (`SELECT` only, single statement, no mutations, no `SELECT INTO`, no locking clauses, table and schema allowlist, function allowlist, no system catalogs). Then execute on a dedicated read-only role, inside a read-only transaction, with a statement timeout, a locked `search_path`, and a row cap.

## Consequences

Defence in depth: the validator and the database each independently prevent harm. The allowlist needs maintenance as features grow.
