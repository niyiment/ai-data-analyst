---
name: add-db-migration
description: Playbook for changing metadata tables in the app schema with Alembic.
---

# Add DB Migration

## When to use

When adding or modifying metadata tables in the `app` or `eval` schemas.

## Key steps

1. Create one reversible Alembic migration for the change.
2. Update the affected repository methods and Pydantic schemas.
3. Update `docs/DATABASE.md` to reflect the schema change.
4. Verify foreign-key `ON DELETE CASCADE` behaviour for session-owned tables.

## Checks

- Migration is reversible (`upgrade` and `downgrade` both tested against PostgreSQL in Docker).
- Session cleanup still removes all session rows and leaves no orphaned metadata.
- Migrations run with `app_owner` in CI/deploy, never from the running API.
