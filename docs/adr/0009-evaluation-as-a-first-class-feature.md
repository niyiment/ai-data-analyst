# ADR-0009: Evaluation is a first-class feature

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

NL-to-SQL quality must be measurable.

## Decision

Golden question sets with reference SQL live in the repo. A runner compares execution results (not SQL text) and reports accuracy, rejection rate, latency, and token cost. The UI exposes it.

## Consequences

Every prompt or model change can be regression-tested. Golden sets run against persistent, read-only demo schemas separate from session data.
