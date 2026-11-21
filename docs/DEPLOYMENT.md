# Deployment and Operations

## 10.1 Environments

| Environment | Frontend | API | Database |
| --- | --- | --- | --- |
| Local | Next.js dev server | Docker container or local run | PostgreSQL in Docker Compose |
| Production | Vercel free tier | Render free web service (Docker) | Neon free tier |

Verify the free-tier terms of each provider just before launch, because they change.

## 10.2 Configuration (names only, values never committed)

**API:**
- `DATABASE_URL_APP`
- `DATABASE_URL_ANALYST`
- `DATABASE_URL_OWNER` *(CI/deploy migrations only; never set on the running API)*
- `LLM_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL` (or another provider's settings, ADR-0013)
- `SESSION_TTL_HOURS`
- `CLEANUP_SECRET`
- `ALLOWED_ORIGIN`
- `RATE_LIMIT_*`, `QUESTIONS_PER_SESSION_PER_HOUR`, `LLM_DAILY_CALL_BUDGET`
- `MAX_UPLOAD_MB`
- `MAX_ROWS`
- `QUERY_TIMEOUT_SECONDS`
- `LOG_LEVEL`

**Web:**
- `API_BASE_URL` (server-side only, for the `/api/*` rewrite)

## 10.3 CI/CD

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `ci.yml` | Every PR; pushes to `main` and `develop` | Guardrails; backend format, lint, types, unit + PostgreSQL integration tests; web format, lint, types, tests, build |
| `cd.yml` | CI succeeded on `main`, or manual | 1) Bootstrap roles (`infra/postgres/bootstrap-roles.sql`, idempotent) and `alembic upgrade head` as the owner role, from GitHub Actions; 2) deploy the **tested commit** to Render through the Render API and wait for `live` + `/health`; 3) `vercel pull/build/deploy --prebuilt --prod`; 4) smoke test through the Vercel proxy (`POST /api/v1/sessions` -> 201, golden sets listed) |
| `preview.yml` | PRs from this repository | Vercel preview deploy; posts the URL on the PR |
| `cleanup.yml` | Every 30 minutes, or manual | `POST /api/v1/internal/cleanup` with the secret header (ADR-0011) |

Deploys are serialized (`concurrency: production`). Render `autoDeploy` is off (`render.yaml`) and Vercel Git deployments are off (`web/vercel.json`), so production only changes through `cd.yml` after CI passes. The owner database URL lives only in GitHub secrets and is never set on Render.

### One-time setup

**Neon:** create the project; copy the owner connection string (with `sslmode=require`).

**Render:** create the service from the `render.yaml` Blueprint and create an API key for the CD workflow. Do not type secrets into the dashboard: before every deploy, `cd.yml` syncs `DATABASE_URL_APP`, `DATABASE_URL_ANALYST`, `CLEANUP_SECRET`, `GEMINI_API_KEY`, `ALLOWED_ORIGIN`, `LLM_PROVIDER`, and `GEMINI_MODEL` from GitHub (failing fast if any is missing) to Render through the Render API.

**Vercel:** import the repository with **Root Directory `web`**; set `API_BASE_URL` (the Render URL) for Production and Preview; create a token. Note the org and project IDs (`vercel link`, or project settings).

**GitHub environment `production`:**

| Kind | Name |
| --- | --- |
| Secret | `DATABASE_URL_OWNER`, `DATABASE_URL_APP` (`app_rw`), `DATABASE_URL_ANALYST` (`analyst_ro`), `APP_RW_PASSWORD`, `ANALYST_RO_PASSWORD`, `GEMINI_API_KEY`, `RENDER_API_KEY`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `CLEANUP_SECRET` |
| Variable | `RENDER_SERVICE_ID`, `API_PUBLIC_URL` (Render URL), `WEB_PUBLIC_URL` (Vercel URL), `LLM_PROVIDER` (`gemini`), `GEMINI_MODEL` (`gemini-3.8-flash`) |

The preview workflow has no environment, so `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` are also needed as repository secrets. `APP_RW_PASSWORD` and `ANALYST_RO_PASSWORD` must match the passwords inside `DATABASE_URL_APP` and `DATABASE_URL_ANALYST`. Use Neon's direct (unpooled) host.

## 10.4 Monitoring and runbook

- **Logging:** Structured logs with request IDs. Track stage timings, rejection rate, and token usage.
- **Cold start:** The UI pings `/health` on load and shows a warming-up state.
- **Gemini quota exceeded:** Return `QUOTA_EXCEEDED` with a retry time, and serve cached answers for identical questions.
- **Database nearly full:** Capacity guard rejects uploads, cleanup runs immediately, check for stuck sessions.
- **Cleanup failure:** Alert through the failed workflow run. The lazy expiry check still protects access.
- **Secret rotation:** Rotate the Gemini key and cleanup secret, redeploy, and verify with `/health`.
