# ADR-0011: Two-layer expiry for 24-hour deletion

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

The free API host has no dependable scheduler.

## Decision

Lazy expiry (an expired session is rejected and purged on access) plus a scheduled GitHub Actions job that calls a secret-protected cleanup endpoint.

## Consequences

Deletion does not depend on one mechanism. The cleanup endpoint must be idempotent and authenticated.
