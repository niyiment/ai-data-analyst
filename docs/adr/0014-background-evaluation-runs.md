# ADR-0014: Evaluation runs execute in the background

- **Status:** Proposed
- **Date:** 2026-11-20

## Context

ADR-0009 makes evaluation a first-class feature. A golden-set run makes one or two model calls per question, and then runs both the generated and the reference SQL. With 33 questions, that adds up to minutes of work. Answering it inside a single HTTP request risks proxy and hosting timeouts (Vercel rewrites, Render free tier), and the user sees nothing until it finishes.

## Decision

- `POST /api/v1/eval/runs` saves a run with status `running` and returns `202 Accepted` immediately.
- A FastAPI `BackgroundTasks` job answers the questions. It opens its own database session, because the request's session closes before background tasks run. It saves progress (results so far, plus running metrics) after every question, and finishes as `completed` or `failed`.
- A failure records a generic message with the exception type only, such as `Evaluation failed (RuntimeError).`. No raw error text is stored or returned.
- Clients poll `GET /api/v1/eval/runs/{id}`. The web Evaluation page shows "Answered X of Y".
- `app.eval_runs` gains `status` and `error` columns, and `finished_at` becomes nullable (migration `0006`). Saving a run is an upsert.

## Consequences

- Requests return quickly, and progress is visible and survives page reloads.
- Jobs run inside the API process. A restart or redeploy during a run leaves it `running` forever. A durable queue or worker is out of scope for the free tier. If this happens in practice, add a staleness rule (for example, mark runs older than N minutes as `failed`).
- Evaluation calls share the API process and the global LLM quota with user questions. The per-IP limit on starting runs (5 per minute) stays in place.
