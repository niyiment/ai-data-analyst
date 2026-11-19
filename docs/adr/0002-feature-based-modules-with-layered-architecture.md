# ADR-0002: Feature-based modules with a router, service, repository layering

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

The requirement is no bloated files and strict separation of concerns.

## Decision

Group backend code by capability (`sessions`, `datasets`, `query`, `charts`, `insights`, `reports`, `evaluation`). Inside each, routers handle HTTP only, services hold business logic, repositories are the only code that touches the database.

## Consequences

More files, but each is small and testable. Dependencies flow one way (router to service to repository). Cross-module calls go through a module's public service interface only.
