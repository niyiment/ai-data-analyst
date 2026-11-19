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
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `SESSION_TTL_HOURS`
- `CLEANUP_SECRET`
- `ALLOWED_ORIGIN`
- `RATE_LIMIT_*`
- `MAX_UPLOAD_MB`
- `MAX_ROWS`
- `QUERY_TIMEOUT_SECONDS`
- `LOG_LEVEL`

**Web:**
- `API_BASE_URL` (server-side only, for the `/api/*` rewrite)

## 10.3 CI/CD

- **On every pull request:** format, lint, type check, file-size and layering checks, unit, integration, API, and security tests.
- **On merge to `main`:** build the API image and deploy to Render; Vercel deploys the web app.
- Run database migrations as a deploy step with the `app_owner` role.
- Scheduled workflow every 30 to 60 minutes calls `POST /api/v1/internal/cleanup` with the secret header.

## 10.4 Monitoring and runbook

- **Logging:** Structured logs with request IDs. Track stage timings, rejection rate, and token usage.
- **Cold start:** The UI pings `/health` on load and shows a warming-up state.
- **Gemini quota exceeded:** Return `QUOTA_EXCEEDED` with a retry time, and serve cached answers for identical questions.
- **Database nearly full:** Capacity guard rejects uploads, cleanup runs immediately, check for stuck sessions.
- **Cleanup failure:** Alert through the failed workflow run. The lazy expiry check still protects access.
- **Secret rotation:** Rotate the Gemini key and cleanup secret, redeploy, and verify with `/health`.
