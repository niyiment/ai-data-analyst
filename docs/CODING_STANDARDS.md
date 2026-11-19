# Coding Standards

## 4.1 Principles

- **One file, one responsibility.** If you cannot name a file's job in a few words, split it.
- **Dependencies flow one way.** Router to service to repository. No upward imports, no circular imports.
- **Explicit over clever.** Prefer clear names and simple control flow.
- **Fail closed.** On any validation doubt, reject.
- **No secrets or user data in logs.**

## 4.2 Size and complexity limits (enforced by lint and CI)

| Item | Target | Hard limit |
| --- | --- | --- |
| File length | 150 lines | 250 lines |
| Function length | 20 lines | 40 lines |
| Function parameters | 4 | 6 (use a typed object beyond that) |
| Cyclomatic complexity | 8 | 12 |
| Nesting depth | 2 | 3 |

A file that grows past the target is split by responsibility, not by arbitrary line count. Exceptions need a comment explaining why.

## 4.3 Backend (Python, FastAPI)

- Python 3.12, fully typed, checked by `mypy` in strict mode. `Ruff` for lint and format.
- Pydantic models for every request, response, and LLM output. No raw dictionaries crossing layer boundaries.
- **Routers:** parse input, call one service method, return a schema. No business logic, no database access.
- **Services:** orchestrate use cases. Receive their dependencies by injection (FastAPI `Depends` or constructor), never import globals.
- **Repositories:** the only place SQL against the metadata database lives. Parameterised queries only. Never build SQL with string formatting.
- Dynamic identifiers (schema, table, column) are generated or sanitised by one shared identifier module and quoted by the driver's identifier API.
- Async all the way for I/O. Blocking work (file parsing) runs in a worker thread or process pool.
- **Errors:** define a small domain exception hierarchy (`ValidationRejected`, `QuotaExceeded`, `NotFound`, `Forbidden`). One global handler maps them to the standard error response. Do not raise `HTTPException` from services.
- **Configuration:** a single typed settings object loaded from environment variables. No `os.environ` reads elsewhere.
- **Logging:** structured JSON with a request ID and session hash. Never log tokens, raw question text at info level, or data values.
- **Prompts:** stored as template files with a version, loaded by a prompt loader. Never inline in service code.

## 4.4 Frontend (Next.js, TypeScript)

- TypeScript strict mode. ESLint and Prettier. No `any`.
- Pages in `app/` are thin: they compose feature components.
- Features live in `features/<name>/` with `components`, `hooks`, `api`, `types`, and an `index.ts` public surface. Other features import only from `index.ts`.
- Server data goes through a typed API client and a data-fetching library. Components never call `fetch` directly.
- Validate every API response at the boundary with a schema library (Zod). The chart mapper only accepts validated specs.
- **Components:** presentational where possible, one component per file, props typed, no more than about 150 lines.
- **Accessibility:** semantic elements, labelled controls, chart data also exposed as a table.

## 4.5 Naming and structure

- **Python:** `snake_case` files, functions, and variables; `PascalCase` classes.
- **TypeScript:** `PascalCase` components, `camelCase` functions, `kebab-case` file names for non-components.
- Names describe intent: `validate_single_statement`, not `check1`.
- Tests mirror the source tree: `tests/query/validator/rules/test_select_only.py`.
- Validator rules: one rule per file, each exposing the same small interface so the pipeline can compose them.

## 4.6 API conventions

- Prefix `/api/v1`. Nouns for resources, plain HTTP verbs.
- One error shape everywhere: `code`, `message`, `details`, `request_id`.
- Pagination and limits on every list endpoint.
- No secrets, tokens, or internal IDs of other sessions in responses.

## 4.7 Git and review

- Trunk-based with short-lived branches. Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`).
- Every pull request needs: description, linked story ID, tests, updated docs if behaviour changed, and a passing CI run.
- **PR checklist:** file and function limits respected, no layering violations, no new unvalidated input, no data in logs, ADR added if a significant decision changed.

## 4.8 Testing rules

- Unit tests for services and rules with fakes for the database and the LLM. Integration tests for repositories against a real PostgreSQL in Docker.
- The SQL validator needs table-driven tests plus an adversarial suite. Every discovered bypass becomes a permanent test.
- No test depends on a live Gemini call. Live calls belong only to the evaluation runner.

## 4.9 Definition of done

Code merged, tests green, lint and type checks green, limits respected, docs and ADRs updated, no new warnings, acceptance criteria of the linked story demonstrably met.
