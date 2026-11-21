# AGENTS.md

These rules guide AI coding assistants working in this repository so generated code follows the same engineering standards.

## Project context

AI Data Analyst turns spreadsheets into queryable tables and answers natural-language questions through a validated, read-only SQL pipeline.

- **Backend:** FastAPI (Python 3.12)
- **Frontend:** Next.js (TypeScript)
- **Database:** PostgreSQL
- **Model:** Gemini behind an `LLMClient` interface

## Always

- Read `docs/CODING_STANDARDS.md` and the relevant ADRs in `docs/adr/` before changing code.
- Keep to the layering: router -> service -> repository. Never access the database from a router.
- Keep files and functions within the size limits (target 150 lines / hard limit 250 lines per file; target 20 / hard limit 40 lines per function). Split by responsibility.
- Add or update tests with every behaviour change. Mirror the source layout.
- Use typed schemas at every boundary. Validate all LLM output.
- Use the shared identifier module for any schema, table, or column name.

## Never

- Build SQL from strings, or run model-generated SQL outside the validator and read-only executor.
- Put secrets, tokens, or data values in logs, URLs, or test fixtures.
- Call Gemini directly from a service. Use the `LLMClient` interface.
- Inline prompts in code. Use the prompt loader.
- Add a dependency without noting why in the pull request.
- Edit an accepted ADR. Add a new one.

## Commands

- Install API: `cd api && uv sync --python 3.12`
- Install web: `cd web && pnpm install`
- Run database: `docker compose up -d postgres`
- Run API: `cd api && uv run uvicorn app.main:app --reload`
- Run web: `cd web && pnpm dev`
- Lint: `cd api && uv run ruff check .` and `cd web && pnpm run lint`
- Type-check: `cd api && uv run mypy src tests` and `cd web && pnpm run typecheck`
- Guardrails: `python scripts/check_limits.py` and `python scripts/check_layering.py`
- Test: `cd api && uv run pytest` and `cd web && pnpm test` (coverage: `pnpm test:coverage`)
- E2E: `cd web && pnpm test:e2e` (needs `docker compose up -d postgres` and migrations; starts an LLM stub, the API on :8001, and the web app on :3100)
- Load: see `loadtest/README.md` (`uv run --with locust locust -f loadtest/locustfile.py ...`)
- Run evaluation: start the API (with migrations applied and an LLM configured), then use the Evaluation page or `POST /api/v1/eval/runs` with `{"set_name": "retail_sales"}`

## Task playbooks (skills)

Task-specific playbooks live in `.claude/skills/`:

- `add-api-endpoint` — Adding a backend endpoint
- `add-validator-rule` — Adding a SQL safety rule
- `add-frontend-feature` — Adding a UI capability
- `add-db-migration` — Changing metadata tables
- `add-golden-question` — Growing the evaluation set
- `tune-prompt` — Changing a prompt
- `write-adr` — Recording a significant architectural decision

## Guardrail hooks (recommended)

- **Pre-commit:** formatter, linter, type check, file-length check.
- **CI:** fails the build if any source file exceeds the hard limit or if an import violates the layering rules (for example, a router importing a repository).

## Before finishing a task

1. Run lint, type checks, and tests.
2. Confirm the linked story's acceptance criteria.
3. Summarise what changed and which docs were updated.
