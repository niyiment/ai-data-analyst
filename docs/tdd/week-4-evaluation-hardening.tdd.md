# TDD evidence: Week 4 evaluation and hardening

- **Branch:** `feat/week-4-evaluation-hardening`
- **Source plan:** none. Journeys were derived during this run from `docs/ROADMAP.md` (Week 4), `docs/USER_STORIES.md` (US-14, US-15), `docs/TESTING.md` §9.2, and the PRD accessibility requirement.
- **Starting point:** a gap audit found that the existing evaluation runner only validated the reference SQL and always reported "correct". Runs were kept in memory, the demo schema did not exist, the golden set had 8 questions, `QuotaGuard` was unused, there was no per-session question limit, and the web app had no test setup.

## User journeys

1. As the operator, I want each session's questions and the total LLM calls capped, so that free tiers survive public traffic and users get a retry time (US-15).
2. As the maintainer, I want evaluation to run each golden question through the real model and pipeline, and to compare execution results, so that accuracy numbers are real (US-14).
3. As the maintainer, I want about 30 golden questions across every category, against a persistent demo schema, so that accuracy is measured broadly (TESTING §9.2).
4. As a keyboard or screen-reader user, I want navigation, status, and answers exposed accessibly (PRD accessibility NFR).

## Task report

| Task | RED commit | RED evidence | GREEN commit | GREEN evidence |
| --- | --- | --- | --- | --- |
| Limits (US-15) | `e6e650f` | `pytest tests/llm/test_quota.py tests/query/test_router_limits.py`: collection `ImportError` (`get_question_rate_limiter`, `app.llm.quota` missing) | `8778bbe` | 5 passed; full suite 94 passed |
| LLM eval runner | `fef85e0` | `pytest tests/evaluation/test_runner.py`: `ModuleNotFoundError: app.evaluation.runner` | `ebfe425` | 8 passed; full suite 102 passed |
| Persisted runs + wiring | `f64c1a4` | `pytest tests/evaluation`: `ModuleNotFoundError: app.evaluation.dependencies`, `ImportError: model_to_run` | `8c1b093` | full suite 107 passed |
| Golden set + demo schema | `c437589` | `pytest tests/evaluation/test_golden_sets.py`: 4 failed (8 questions, categories missing, migration 0005 absent), 9 passed | `b9d03ed` | full suite 145 passed |
| Accessibility | `2fae9ba` | `pnpm test`: 7 failed, 1 passed (no skip link, unlabelled nav, no `aria-expanded`, no progress bar, axe `heading-order`, no conversation log / `aria-busy`) | `8ebbce0` | 8 passed |
| CI + formatting | n/a | n/a | `a03bc69` | frozen install exit 0; format:check, lint, typecheck, test, build all pass |

## Test specification

| # | What is guaranteed | Test | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | A session over its hourly question budget gets 429 `RATE_LIMITED` with `retry_after_seconds`, and the query service never runs | `api/tests/query/test_router_limits.py` | API | PASS |
| 2 | Every request's LLM client spends the global daily budget, and an exhausted budget raises `QUOTA_EXCEEDED` without calling the model | `api/tests/llm/test_quota.py` | unit | PASS |
| 3 | Matching execution results count as correct; different results count as `wrong_result` | `api/tests/evaluation/test_runner.py` | unit | PASS |
| 4 | Unsafe generated SQL is `validator_rejected` and never executed | `test_runner.py::test_unsafe_sql_is_rejected_and_never_executed` | unit | PASS |
| 5 | Provider failures are `llm_error`; timeouts and DB errors are `execution_error` | `test_runner.py` | unit | PASS |
| 6 | Ambiguity questions pass only if the model asks for clarification; unexpected or missed clarifications are wrong | `test_runner.py` | unit | PASS |
| 7 | Runs map losslessly to and from the `eval_runs` row | `api/tests/evaluation/test_repository.py` | unit | PASS |
| 8 | Production wiring uses the SQL repository, the LLM runner, and a `provider:model` label | `api/tests/evaluation/test_dependencies.py` | unit | PASS |
| 9 | Golden set has at least 30 unique questions covering all 7 categories | `api/tests/evaluation/test_golden_sets.py` | unit | PASS |
| 10 | All 33 reference SQL queries pass the production AST validator | `test_golden_sets.py::test_reference_sql_passes_the_production_validator` | unit | PASS (33) |
| 11 | The schema summary matches migration 0005's tables and columns; the seed data is internally consistent | `test_golden_sets.py` | unit | PASS |
| 12 | WorkspaceShell has no axe violations, and has a skip link, `aria-current`, `aria-expanded`/`aria-controls`, and a labelled progress bar | `web/src/features/datasets/components/WorkspaceShell.test.tsx` | component | PASS |
| 13 | QueryPanel has no axe violations, a labelled live conversation log, `aria-busy` while running, and the visible button state as its accessible name | `web/src/features/query/components/QueryPanel.test.tsx` | component | PASS |

## Coverage and known gaps

- **Backend coverage:** `uv run --with pytest-cov pytest --cov=app`: 85% total. On changed modules: `runner.py` 100%, `dependencies.py` 100%, `quota.py` 100%, `factory.py` 100%, `service.py` 98%, `query/dependencies.py` 95%, `repository.py` 82%. The uncovered code is `SqlEvalRepository`, which needs a database.
- **Frontend coverage:** not measured (`@vitest/coverage-v8` is not installed).
- **Not verified against a live PostgreSQL:** Docker was not running. Migrations `0004` and `0005`, `SqlEvalRepository`, and the 33 reference queries executing on the real demo schema remain unverified. Ranking ties were checked against the seed data with SQLite.
- **Tokens:** `tokens_in` and `tokens_out` are reported as 0, because the `LLMClient` port does not expose token usage.
- **Contrast:** jsdom cannot compute colour contrast, so the axe contrast rule does not run in tests. It was checked manually instead: `#64748b` on white is about 4.8:1, and `#94a3b8` on `#0b1220` is about 7.6:1.
- **Not covered by tests:** pages other than the shell and the AI Analyst panel. Their headings changed (CardTitle now renders `h2`), but they have no component tests.
- **Found but out of scope:** the UI refresh dropped chart rendering (`ChartRenderer` is unused). The plan-stage skip for simple questions is not implemented.

## Addendum: gaps closed (2026-11-20)

| Gap | RED evidence | GREEN commit | Result |
| --- | --- | --- | --- |
| Live PostgreSQL unverified | n/a (verification) | `d4ed131` | Applied `0004`/`0005`; 38 integration tests passed (33 references as `analyst_ro`, known answers, repository round trip) |
| Charts never wired end to end | pytest 3 failed (no `chart_spec`); vitest 1 failed (no figure) | `d3259c4` | Validated chart spec returned and rendered as a captioned figure next to the table |
| Plan stage never skipped | ImportError `should_skip_plan`; path tests failed | `3040405`, `eab14a1` | Simple single-table questions take one LLM call; `accuracy_by_path`; `retail_orders` set covers the direct path |
| Token usage reported as 0 | ModuleNotFoundError `app.llm.usage` | `6b4c24e` | Ollama, Claude, and Gemini record usage; per-question tokens |
| Eval request timeout risk | ImportError `get_eval_job`; vitest 2 failed (no status/alert) | `e889dfa`, `47e0fa3` | 202 + background run with saved progress; UI polls |
| Orphaned running runs | 1 failed (stayed `running`) | `26921ad` | Reported as interrupted after 60 min |
| Accessibility tests limited to two components | vitest 1 failed (ReportsView `heading-order`) | `4da0f88` | axe on every page component (23, then 25 tests) |
| Web coverage unmeasured | n/a | `f4d7081` | 84.1% statements, 77.1% branches (workspace integration test fakes only `fetch`) |
| Integration tests skipped in CI | n/a | `7139d9c` | CI PostgreSQL service; rehearsed: `0001`→`0006` from empty, 262 passed with 0 skipped, downgrade/upgrade round trip |
| No ADR for providers or background runs | n/a | `5168c29` | ADR-0013 and ADR-0014 (Proposed) |

**Live evaluation (local `ollama:llama3.2`):** `retail_orders` completed at 38.5% (26/26, all on the direct path, tokens recorded). `retail_sales` was stopped at 11/33 (27.3% so far) because the machine ran low on memory. That stopped run exposed the orphaned-run gap fixed in `26921ad`.

**Final checks:** pytest 264 passed; vitest 25 passed; ruff, mypy, eslint, tsc, prettier, `check_limits`, and `check_layering` all clean.
