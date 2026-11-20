# Testing and Evaluation

## 9.1 Test layers

| Layer | Scope | Tooling | Where / command |
| --- | --- | --- | --- |
| Unit | Services, validator rules, sanitiser, type inference, chart-spec validator, LLM adapters, API client, chart mapper | `pytest` with fakes; `Vitest` | `api/tests/**`, `web/src/**/*.test.ts`; `uv run pytest`, `pnpm test` |
| Component | Each page and widget: behaviour plus axe accessibility checks | `Vitest`, Testing Library, `vitest-axe` | `web/src/**/*.test.tsx`; `pnpm test`, `pnpm test:coverage` |
| Integration | HTTP flows over real PostgreSQL (repositories, DDL, executor, isolation, cleanup); golden reference SQL as `analyst_ro` | `pytest` + ASGI client; skipped when PostgreSQL is unreachable; runs in CI | `api/tests/integration/` |
| Security | Adversarial SQL and authorisation suites | `pytest`, run in CI on every change | `api/tests/query/validator/`, integration isolation tests |
| End to end | Browser -> Next.js -> API -> PostgreSQL user journeys, keyboard skip link, axe WCAG A/AA (incl. contrast) | Playwright with a deterministic Ollama-compatible LLM stub (`web/e2e/llm-stub.mjs`) | `web/e2e/`; `pnpm test:e2e` (needs PostgreSQL + migrations) |
| Load | Concurrent sessions: sample load, questions, history and detail reads; fails on >1% errors or p95 > 1.5 s | Locust (not a project dependency) | `loadtest/`; see `loadtest/README.md` |
| Evaluation | Golden sets with the live model | Runner, scheduled or manual, never in unit CI | Evaluation page or `POST /api/v1/eval/runs` |

## 9.2 Evaluation design

- **Golden sets:** Around 30 questions per demo dataset, grouped by category (filter, aggregate, group by, join across sheets, date logic, ranking, ambiguity) and difficulty.
- **Correctness:** Compare *execution results* of generated and reference SQL, normalising column order and, unless the question demands order, row order.
- **Metrics:** Execution accuracy, validator rejection rate, clarification rate, failure categories, p50 and p95 latency, tokens per question.
- **Baselines:** Store every run with its prompt version and model so changes can be compared.
- **Gate:** A change to prompts or pipeline merges only if accuracy does not drop beyond an agreed tolerance.
