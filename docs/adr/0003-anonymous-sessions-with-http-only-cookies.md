# ADR-0003: Anonymous sessions with opaque tokens in HTTP-only cookies

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

No accounts, but data must be owned and isolated.

## Decision

The server issues a random opaque token, stores only its hash, and sets it as a `Secure`, `HttpOnly`, `SameSite` cookie. Tokens never appear in URLs, logs, or response bodies.

## Consequences

Protects against token leakage and script access. Requires CSRF protection on state-changing requests and a same-origin setup (see [ADR-0010](0010-same-origin-proxy-for-cookies.md)).
