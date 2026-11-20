# AI Data Analyst

Upload a CSV or Excel spreadsheet, ask questions in plain English, and receive a verified, inspectable answer: the query plan, generated read-only SQL, result table, interactive chart, on-demand written insights, and an exportable PDF/HTML report.

Built to production-grade engineering standards on free cloud tiers, with defence-in-depth SQL safety, anonymous 24-hour sessions, and first-class NL-to-SQL evaluation.

---

## Key Features

- **Spreadsheet to queryable tables:** Upload CSV or multi-sheet XLSX files (up to 10 MB). Each sheet becomes a sanitised PostgreSQL table in an isolated per-dataset schema.
- **Schema review & sample data:** Inspect inferred column types and preview rows, rename columns or override types before querying, or load built-in sample datasets in one click.
- **Two-stage NL-to-SQL pipeline:** Complex questions produce a structured query plan before SQL generation (simple single-table questions skip the plan stage to save latency and quota). Ambiguous questions trigger a targeted clarification with selectable options.
- **Defence-in-depth SQL safety:** Every generated query passes a SQLGlot AST validator pipeline (allowlists, single `SELECT` only, no mutations, no locking, no system catalogs) and executes on a dedicated `analyst_ro` PostgreSQL role inside a read-only transaction with a locked `search_path`, statement timeout, and row cap.
- **Safe visualisations & insights:** The LLM returns a typed chart specification validated against actual result columns and rendered with Apache ECharts (falling back to the table if invalid). Insights are generated on demand strictly from the capped result set.
- **Exportable reports:** Pin answers into a report (question, SQL, table, chart, insights) and download as PDF or HTML.
- **First-class evaluation:** Built-in evaluation page and runner that executes golden question sets against persistent demo schemas and tracks execution accuracy, validator rejection rate, latency, and token cost.
- **Privacy by default:** Anonymous sessions via `Secure`, `HttpOnly`, `SameSite` cookies—no accounts, no tokens in URLs. All session data is automatically purged after 24 hours, with a one-click **"Delete my data now"** action.

---

## Architecture

```mermaid
flowchart LR
    Browser["Browser (Next.js UI)"] -->|Same-origin /api/*| Proxy["Next.js Rewrite Proxy (Vercel)"]
    Proxy --> API["FastAPI Backend (Render)"]

    subgraph API_Layers["FastAPI Feature Modules"]
        Router["Routers (HTTP only)"] --> Service["Services (Use cases)"]
        Service --> Repo["Repositories (Metadata SQL)"]
        Service --> LLM["LLMClient Port (Ollama / Gemini / Claude)"]
        Service --> Validator["SQLGlot AST Validator"]
        Validator --> Executor["Read-Only Executor"]
    end

    API --> Router
    Repo -->|app_rw role| PG_App[("PostgreSQL: app schema")]
    Executor -->|analyst_ro role| PG_DS[("PostgreSQL: ds_* & demo_* schemas")]
    GHA["GitHub Actions (Scheduled Cleanup)"] -->|POST /api/v1/internal/cleanup| API
```

### Core Architectural Principles

- **Strict layering:** `router -> service -> repository`. Routers handle HTTP only; services orchestrate use cases; repositories are the only layer touching metadata SQL.
- **Provider independence:** All LLM calls go through an `LLMClient` interface with versioned prompt templates loaded from files. Adapters exist for Ollama (local or cloud), Gemini, and Claude; the default comes from `LLM_PROVIDER`, and a request can override provider, model, and API key with the `X-LLM-Provider`, `X-LLM-Model`, and `X-LLM-Api-Key` headers.
- **Same-origin cookies:** Next.js proxies `/api/*` to the FastAPI backend so cookies remain first-party across free-tier hosts.
- **Two-layer data expiry:** Lazy expiry on access plus a scheduled GitHub Actions cleanup job calling an authenticated, idempotent cleanup endpoint.

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| **Frontend** | Next.js (TypeScript strict mode), Apache ECharts, Zod, Vitest, Playwright |
| **Backend** | FastAPI (Python 3.12), Pydantic, SQLGlot, Alembic, `mypy` (strict), `Ruff`, `pytest` |
| **Database** | PostgreSQL (Docker Compose locally; Neon free tier in production) |
| **LLM** | Ollama (local or cloud, default), Google Gemini, or Anthropic Claude behind an `LLMClient` port |
| **Hosting & CI** | Vercel (web), Render (API Docker container), GitHub Actions (CI & scheduled cleanup) |

---

## Repository Structure

```text
ai-data-analyst/
├── api/                 # FastAPI backend (feature-based modules, migrations, prompts, tests)
├── web/                 # Next.js frontend (thin app/ pages, features/<name>/ modules)
├── docs/                # Engineering documentation & ADRs
│   └── adr/             # Architecture Decision Records (0000–0012)
├── .claude/skills/      # Task-specific AI coding playbooks
├── AGENTS.md            # Root rules for AI coding assistants
└── README.md
```

> **Status:** Weeks 0–4 are implemented: sessions and ingestion, the safe query core, charts, insights, reports, LLM-backed evaluation against a persistent demo schema (33 golden questions), per-session question limits, a global LLM quota guard, and an accessibility pass. Remaining work is Week 5 (production deploy, scheduled cleanup workflow, published accuracy results). See [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Security & Privacy

- **Zero cross-session access:** Each dataset lives in a server-generated schema (`ds_<random hex>`). Every resource ID is resolved through the current session; unauthorised IDs return `NOT_FOUND`.
- **Prompt injection resilience:** Sampled cell values are treated as untrusted data. Safety is enforced by the AST validator and PostgreSQL role privileges, never by prompt instructions.
- **No secrets or user data in logs:** Structured JSON logs include only request IDs, session hashes, stage timings, and error codes.
- **Export safety:** Leading formula characters (`=`, `+`, `-`, `@`) are neutralised in exported reports/CSV, and all rendered output is escaped under strict CSP headers.

See [docs/SECURITY.md](docs/SECURITY.md) for the full threat model.

---

## Initial Limits (Defaults)

| Limit | Default |
| --- | --- |
| Upload size | 10 MB |
| Rows per sheet | 100,000 |
| Columns per sheet | 100 |
| Sheets per file | 5 |
| Datasets per session | 3 |
| Result rows returned | 1,000 |
| Query timeout | 10 seconds |
| Questions per session / hour | 30 (`QUESTIONS_PER_SESSION_PER_HOUR`) |
| LLM calls per day (all sessions) | 1,000 (`LLM_DAILY_CALL_BUDGET`) |
| Session lifetime | 24 hours |

---

## Getting Started (Local Development)

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ and [`uv`](https://docs.astral.sh/uv/)
- Node.js 20+ and [`pnpm`](https://pnpm.io/)
- An LLM: a local [Ollama](https://ollama.com/) install (the default), or an API key for Ollama Cloud, Gemini, or Claude

### 1. Configure environment variables

Copy `.env.example` to `.env`, set `LLM_PROVIDER` (`ollama`, `ollama_cloud`, `gemini`, or `claude`), and fill in that provider's settings, e.g. `OLLAMA_MODEL`, `GEMINI_API_KEY`, or `ANTHROPIC_API_KEY` (never commit `.env`):

```bash
cp .env.example .env
```

### 2. Start PostgreSQL and run migrations

```bash
docker compose up -d postgres
```

Wait until the `postgres` container reports `healthy` (`docker compose ps`), then run Alembic migrations using the owner role:

```bash
# Bash / macOS / Linux
export DATABASE_URL_OWNER="postgresql+psycopg://app_owner:local_owner_password@localhost:5433/ai_data_analyst"
cd api && uv sync --python 3.12 && uv run alembic upgrade head
```

```powershell
# Windows PowerShell
$env:DATABASE_URL_OWNER = "postgresql+psycopg://app_owner:local_owner_password@localhost:5433/ai_data_analyst"
cd api; uv sync --python 3.12; uv run alembic upgrade head
```

### 3. Run the API and Web apps

In terminal 1 (Backend — `http://localhost:8000`):

```bash
cd api
uv run uvicorn app.main:app --reload
```

In terminal 2 (Frontend — `http://localhost:3000`):

```bash
cd web
pnpm install
pnpm dev
```

*(Alternatively, run both PostgreSQL and the API container together with `docker compose up -d`.)*

### 4. Verify lint, types, guardrails, and tests

```bash
# Backend
cd api && uv run ruff check . && uv run mypy src tests && uv run pytest

# Frontend
cd web && pnpm run lint && pnpm run typecheck

# Repository guardrails (file/function size limits & layering)
python scripts/check_limits.py
python scripts/check_layering.py
```

---

## Deployment (Production)

The production stack runs on free cloud tiers with zero hardcoded provider logic (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) and [ADR-0012](docs/adr/0012-free-tier-hosting-choices.md)):

| Component | Host | Notes |
| --- | --- | --- |
| **Database** | Neon (PostgreSQL) | Create `app_owner`, `app_rw`, and `analyst_ro` roles via `infra/postgres/init-roles.sql` |
| **API** | Render (Docker web service) | Root directory `api/`; runs FastAPI container |
| **Frontend** | Vercel (Next.js) | Root directory `web/`; rewrites `/api/*` to `API_BASE_URL` so cookies stay same-origin |
| **Cleanup** | GitHub Actions | Scheduled every 30–60 min calling `POST /api/v1/internal/cleanup` with `CLEANUP_SECRET` |

### Required Environment Variables

- **API (Render):** `DATABASE_URL_APP` (`app_rw`), `DATABASE_URL_ANALYST` (`analyst_ro`), `LLM_PROVIDER` plus that provider's settings (`OLLAMA_CLOUD_BASE_URL` / `OLLAMA_CLOUD_API_KEY` / `OLLAMA_CLOUD_MODEL`, `GEMINI_API_KEY` / `GEMINI_MODEL`, or `ANTHROPIC_API_KEY` / `CLAUDE_MODEL`), `SESSION_TTL_HOURS`, `CLEANUP_SECRET`, `ALLOWED_ORIGIN`, `QUESTIONS_PER_SESSION_PER_HOUR`, `LLM_DAILY_CALL_BUDGET`, `MAX_UPLOAD_MB`, `MAX_ROWS`, `QUERY_TIMEOUT_SECONDS`, `LOG_LEVEL`
- **Migrations (CI / deploy step only):** `DATABASE_URL_OWNER` (`app_owner`) — never set on the running API service
- **Web (Vercel):** `API_BASE_URL` (server-side only, pointing to the Render API URL)

### Deployment Checklist

1. Provision Neon PostgreSQL and apply `infra/postgres/init-roles.sql`.
2. Run `cd api && uv run alembic upgrade head` with `DATABASE_URL_OWNER`.
3. Deploy `api/` to Render and verify `GET /api/v1/health`.
4. Deploy `web/` to Vercel with `API_BASE_URL` set to the Render URL.
5. Configure `API_BASE_URL` and `CLEANUP_SECRET` in GitHub Actions secrets for the scheduled cleanup workflow.

---

## Testing & Evaluation

- **Unit & API tests:** `pytest` with fake DB/LLM adapters (backend) and `Vitest` + Testing Library with automated `axe` accessibility checks (frontend). No unit test ever calls a live LLM provider.
- **Integration & security tests:** `pytest` against PostgreSQL in Docker, including an adversarial SQL suite (100% block target) and cross-session authorisation tests.
- **End-to-end tests:** Playwright against the local stack.
- **Evaluation:** Golden question sets (~30 questions per demo dataset) compared by *execution result* rather than SQL text, targeting at least **80% execution accuracy** (90% stretch). Run them from the Evaluation page or via `POST /api/v1/eval/runs`.

See [docs/TESTING.md](docs/TESTING.md) for details.

---

## Engineering Documentation

| Document | Description |
| --- | --- |
| [docs/PRD.md](docs/PRD.md) | Product requirements, non-goals, limits, success metrics, and risks |
| [docs/USER_STORIES.md](docs/USER_STORIES.md) | User stories and acceptance criteria across Epics A–F |
| [docs/adr/](docs/adr/) | Architecture Decision Records (`0001`–`0012`) and template (`0000`) |
| [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) | Layering rules, file/function size limits, conventions, and Definition of Done |
| [docs/DATABASE.md](docs/DATABASE.md) | Schemas, roles (`app_owner`, `app_rw`, `analyst_ro`), tables, indexes, and cleanup |
| [docs/API.md](docs/API.md) | `/api/v1` endpoints, standard error shape, and ownership rules |
| [docs/SECURITY.md](docs/SECURITY.md) | Threat model, mitigations, and security test suites |
| [docs/TESTING.md](docs/TESTING.md) | Test pyramid and golden-set evaluation design |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Environments, configuration, CI/CD, and operational runbook |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 6-week delivery plan (Weeks 0–5) |
| [AGENTS.md](AGENTS.md) | Rules and guardrails for AI coding assistants |

---

## Roadmap

| Week | Milestone | Status |
| --- | --- | --- |
| **0** | Foundations: docs, repo scaffold, CI (lint, type, size, layering), Docker Compose | Done |
| **1** | Sessions & ingestion: cookie sessions, upload, schema inference, per-dataset schemas, cleanup | Done |
| **2** | Safe query core: AST validator (100% adversarial block), read-only executor, plan/SQL pipeline | Done |
| **3** | Charts, insights & reports: ECharts spec validation, on-demand insights, PDF/HTML export | Done |
| **4** | Evaluation & hardening: golden sets, eval UI, rate limits, quota guard, accessibility | Done (live-database verification pending) |
| **5** | Deploy & polish: Vercel + Render + Neon production deploy, scheduled cleanup, demo | Not started |
