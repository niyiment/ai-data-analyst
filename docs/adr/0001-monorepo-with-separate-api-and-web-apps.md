# ADR-0001: Monorepo with separate `api` and `web` apps

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

One developer, two deployable apps that share a contract.

## Decision

A single repository with `api/`, `web/`, `docs/`, and CI at the root.

## Consequences

Atomic changes across API and UI, one CI pipeline, simple onboarding. Deployments must be path-filtered so each app builds only when it changes.
