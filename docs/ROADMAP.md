# Roadmap

| Week | Milestone | Exit criteria | Status |
| --- | --- | --- | --- |
| 0 | Foundations | Docs approved, repo scaffold, CI with lint, type, size, and layering checks, Docker Compose | Done |
| 1 | Sessions and ingestion | Cookie sessions, upload, schema inference, per-dataset schemas, cleanup endpoint, schema review UI | Done |
| 2 | Safe query core | Validator with adversarial suite at 100%, read-only executor, plan and SQL stages behind the LLM port, results UI | Done (the plan stage is skipped for simple single-table questions) |
| 3 | Charts, insights, reports | Chart spec validation and ECharts rendering, insights, report export | Done (charts are now returned with query results and rendered) |
| 4 | Evaluation and hardening | Golden sets, eval page, rate limits, quota guard, accessibility pass | Done; verified against live PostgreSQL and a local model |
| 5 | Deploy and polish | Production deploy, scheduled cleanup verified, README with architecture diagram, demo video, accuracy results published | Not started (README architecture diagram already in place) |

The `LLMClient` port has adapters for Ollama (local and cloud), Gemini, and Claude (ADR-0013).

## Week 4 delivered

- **Evaluation:** an LLM-backed runner uses the production prompts, validator, and read-only executor, and compares execution results. There are two golden sets on the persistent `demo_retail_sales` schema: `retail_sales` (33 questions, planned path) and `retail_orders` (26 questions, direct path). Runs record accuracy per path and tokens per question. They execute in the background with saved progress, and orphaned runs are reported as interrupted (ADR-0014).
- **Limits:** a per-session question limit, and a global daily LLM call budget on every provider call.
- **Accessibility:** axe checks on every page component in CI, a skip link, labelled navigation with `aria-current`, an announced conversation log, labelled progress, and a valid heading outline.
- **Verification:** migrations `0001`–`0006` apply from an empty database. All 59 reference queries run as `analyst_ro`. CI now runs these PostgreSQL integration tests.

## First live results (local `ollama:llama3.2`, 3B)

| Set | Answered | Accuracy | Notes |
| --- | --- | --- | --- |
| `retail_orders` (direct path) | 26 / 26 | 38.5% | p50 4.2 s, p95 11.7 s; 4,795 tokens in / 890 out; 15 wrong results, 1 execution error, 0 validator rejections |
| `retail_sales` (planned path) | 11 / 33 | 27.3% so far | Stopped partway: Claude Code ended the process because the machine ran low on memory |

These numbers measure a small local model, not the target. Week 5 publishes results for the production model.

## Next steps

1. Rerun `retail_sales` when the machine has memory to spare, and run both sets with the production model (for example, Gemini) to publish accuracy.
2. Accept or revise ADR-0013 and ADR-0014 (currently Proposed).
3. Week 5: deploy to Neon, Render, and Vercel; add the scheduled cleanup GitHub Actions workflow and verify it; publish accuracy results; record the demo video.
