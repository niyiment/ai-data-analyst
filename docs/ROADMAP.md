# Roadmap

| Week | Milestone | Exit criteria | Status |
| --- | --- | --- | --- |
| 0 | Foundations | Docs approved, repo scaffold, CI with lint, type, size, and layering checks, Docker Compose | Done |
| 1 | Sessions and ingestion | Cookie sessions, upload, schema inference, per-dataset schemas, cleanup endpoint, schema review UI | Done |
| 2 | Safe query core | Validator with adversarial suite at 100%, read-only executor, plan and SQL stages behind the LLM port, results UI | Done |
| 3 | Charts, insights, reports | Chart spec validation and ECharts rendering, insights, report export | Done (workspace UI refresh in progress) |
| 4 | Evaluation and hardening | Golden sets, eval page, rate limits, quota guard, accessibility pass | Done, except the accessibility pass |
| 5 | Deploy and polish | Production deploy, scheduled cleanup verified, README with architecture diagram, demo video, accuracy results published | Not started (README architecture diagram already in place) |

Beyond the original plan, the `LLMClient` port now has adapters for Ollama (local and cloud), Gemini, and Claude, selectable by configuration or per request.

## Next steps

1. Finish and commit the workspace UI refresh on `feat/week-3-charts-insights-reports`.
2. Complete the Week 4 accessibility pass.
3. Record the multi-provider LLM selection in a new ADR (ADR-0007 covers the port, but not the choice of providers).
4. Week 5: deploy to Neon, Render, and Vercel; add the scheduled cleanup GitHub Actions workflow and verify it; publish golden-set accuracy results; record the demo video.
