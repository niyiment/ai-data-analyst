# ADR-0012: Free-tier hosting choices

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

Capstone with zero budget.

## Decision

Neon for PostgreSQL (permanent free tier), Render for the FastAPI container, Vercel for Next.js. Docker Compose for local development. Re-verify free-tier terms before launch.

## Consequences

Cold starts on the API and a small database. All provider specifics stay in configuration.
