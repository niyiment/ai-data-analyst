# ADR-0004: One generated PostgreSQL schema per uploaded dataset

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

Isolation and easy deletion.

## Decision

Each dataset gets a schema named from a server-generated random identifier (never from user input). Tables and columns inside use sanitised, collision-safe names.

## Consequences

Dropping a schema deletes everything for that dataset. Ownership is enforced by mapping session to dataset to schema in metadata. Many schemas on a small free database is acceptable at demo scale.
