# ADR-0008: Structured chart specifications rendered by Apache ECharts

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

Free-form chart code from a model is unsafe and unreliable.

## Decision

The model returns a typed spec (chart type, x, y, series, title). The backend validates it against the result's columns and types. The frontend maps a valid spec to an ECharts option. Invalid specs fall back to the table.

## Consequences

No model-generated code executes anywhere. The set of supported chart types is explicit and testable.
