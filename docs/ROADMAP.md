# Roadmap

| Week | Milestone | Exit criteria |
| --- | --- | --- |
| 0 | Foundations | Docs approved, repo scaffold, CI with lint, type, size, and layering checks, Docker Compose |
| 1 | Sessions and ingestion | Cookie sessions, upload, schema inference, per-dataset schemas, cleanup endpoint, schema review UI |
| 2 | Safe query core | Validator with adversarial suite at 100%, read-only executor, plan and SQL stages behind the LLM port, results UI |
| 3 | Charts, insights, reports | Chart spec validation and ECharts rendering, insights, report export |
| 4 | Evaluation and hardening | Golden sets, eval page, rate limits, quota guard, accessibility pass |
| 5 | Deploy and polish | Production deploy, scheduled cleanup verified, README with architecture diagram, demo video, accuracy results published |

## Next steps

1. Review and approve these engineering docs, and confirm the two settled PRD decisions (on-demand insights; skipping the plan stage for simple single-table questions).
2. Generate the repository scaffold: folder skeleton, configuration, CI, and empty module files that respect the size and layering rules.
3. Begin Week 1 with the session and ingestion modules.
