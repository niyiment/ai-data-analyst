# Roadmap

| Week | Milestone | Exit criteria | Status |
| --- | --- | --- | --- |
| 0 | Foundations | Docs approved, repo scaffold, CI with lint, type, size, and layering checks, Docker Compose | Done |
| 1 | Sessions and ingestion | Cookie sessions, upload, schema inference, per-dataset schemas, cleanup endpoint, schema review UI | Done |
| 2 | Safe query core | Validator with adversarial suite at 100%, read-only executor, plan and SQL stages behind the LLM port, results UI | Done (the plan stage still runs for every question; skipping it for simple single-table questions is not implemented) |
| 3 | Charts, insights, reports | Chart spec validation and ECharts rendering, insights, report export | Done, with a regression: the UI refresh no longer renders `ChartRenderer`, so answers show tables but no charts |
| 4 | Evaluation and hardening | Golden sets, eval page, rate limits, quota guard, accessibility pass | Done; migrations `0004`/`0005` and a live evaluation run still need verifying against PostgreSQL |
| 5 | Deploy and polish | Production deploy, scheduled cleanup verified, README with architecture diagram, demo video, accuracy results published | Not started (README architecture diagram already in place) |

Beyond the original plan, the `LLMClient` port now has adapters for Ollama (local and cloud), Gemini, and Claude, selectable by configuration or per request.

## Week 4 delivered

- **Evaluation:** an LLM-backed runner sends each golden question through the production plan and SQL prompts, validates the generated SQL, executes it and the reference SQL read-only on `analyst_ro`, and compares results. Runs persist in `app.eval_runs`. The `retail_sales` golden set has 33 questions across filter, aggregate, group by, join, date logic, ranking, and ambiguity, against the persistent `demo_retail_sales` schema.
- **Limits:** a per-session question limit on `POST /datasets/{id}/queries`, and a global daily LLM call budget applied to every provider call.
- **Accessibility:** Vitest with axe checks in CI, a skip link, labelled navigation with `aria-current`, an announced conversation log, a labelled quota progress bar, and a valid heading outline.

## Next steps

1. Start PostgreSQL, run `alembic upgrade head`, and run one evaluation of `retail_sales` with a live model to verify migrations `0004`/`0005` end to end.
2. Restore chart rendering in query answers (Week 3 regression).
3. Record the multi-provider LLM selection in a new ADR (ADR-0007 covers the port, but not the choice of providers).
4. Week 5: deploy to Neon, Render, and Vercel; add the scheduled cleanup GitHub Actions workflow and verify it; publish golden-set accuracy results; record the demo video.
