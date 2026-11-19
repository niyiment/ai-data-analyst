---
name: add-api-endpoint
description: Playbook for adding a new backend API endpoint following router, service, repository layering.
---

# Add API Endpoint

## When to use

When adding a new backend endpoint under `/api/v1`.

## Key steps

1. Define Pydantic request and response schemas.
2. Add a repository method if database access is needed (parameterised queries only).
3. Add a service method implementing the use case (receive dependencies via injection).
4. Add a thin router handler that parses input, calls one service method, and returns the response schema.
5. Map any new domain exceptions in the global error handler (never raise `HTTPException` from services).
6. Document the endpoint in `docs/API.md`.

## Checks

- Router contains no business logic and no database access.
- Unit tests cover the service; API tests cover the router, ownership rules, and error shape (`code`, `message`, `details`, `request_id`).
- File and function size limits are respected.
