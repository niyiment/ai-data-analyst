# ADR-0007: LLM access behind a port (interface)

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

Testability and provider independence.

## Decision

Services depend on an `LLMClient` interface. Gemini is one adapter. Tests use a fake adapter.

## Consequences

No network calls in unit tests. Prompts live in versioned template files, not inline strings.
