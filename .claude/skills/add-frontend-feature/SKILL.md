---
name: add-frontend-feature
description: Playbook for adding a new feature module to the Next.js frontend.
---

# Add Frontend Feature

## When to use

When adding a new UI capability in `web/`.

## Key steps

1. Create `features/<name>/` with `components/`, `hooks/`, `api/`, `types/`, and an `index.ts` public surface.
2. Route all server requests through the typed API client and validate every response at the boundary with Zod.
3. Compose the feature in a thin page inside `app/`.

## Checks

- No cross-feature deep imports (import only from another feature's `index.ts`).
- Components never call `fetch` directly and stay within ~150 lines.
- All API responses are validated with Zod; chart data is also exposed as an accessible table.
