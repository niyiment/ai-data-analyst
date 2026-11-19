# ADR-0010: Same-origin proxy so cookies work across free hosts

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

The web app (Vercel) and API (Render) are different sites, and browsers block many cross-site cookies.

## Decision

The browser talks only to the web origin. Next.js rewrites `/api/*` to the backend. Cookies are set for the web origin.

## Consequences

Reliable cookies and no CORS surface. Adds one proxy hop of latency. Revisit with a custom domain.
