# Product Requirements Document (PRD)

**Version:** 0.1 · **Date:** 19 Nov 2026 · **Status:** Draft for review · **Author:** Adeniyi

> Numbers (limits, timeouts, quotas) are initial defaults to be tuned during build and evaluation.

## 1.1 Overview

AI Data Analyst lets a person upload a CSV or Excel file, ask questions in plain English, and receive a verified answer: the generated SQL, a result table, a chart, written insights, and an exportable report. It is a portfolio capstone built to production-grade standards on free cloud tiers.

## 1.2 Problem

People hold valuable data in spreadsheets but cannot write SQL. Existing AI tools often hide how an answer was produced, which makes the answer hard to trust, and they rarely explain what happens to uploaded data.

## 1.3 Goals

- Turn a natural-language question into a correct, safe, read-only SQL query.
- Make every answer inspectable: plan, SQL, and result are always visible.
- Protect user data: anonymous sessions, isolation, automatic deletion after 24 hours.
- Make quality measurable: evaluation is a visible feature, not a private script.
- Stay maintainable: layered, feature-based code with small single-purpose files.

## 1.4 Non-goals (MVP)

- User accounts, login, or billing.
- Multi-file joins across separate uploads.
- Write queries or data editing.
- Saved dashboards or long-term storage.
- Public shareable report links (reports are downloaded, not hosted).
- Real-time collaboration.

## 1.5 Target users

| Persona | Need |
| --- | --- |
| Small-business owner | Understand sales or expenses without learning SQL |
| Analyst or student | Explore a dataset fast and check the SQL |
| Capstone reviewer or recruiter | Try the product in under two minutes and see engineering quality |

## 1.6 Functional requirements

| ID | Requirement |
| --- | --- |
| FR-01 | Create an anonymous session automatically on first visit, tracked by a Secure, HTTP-only cookie. No tokens in URLs. |
| FR-02 | Upload a CSV or XLSX file within size limits. Each sheet becomes one table. |
| FR-03 | Show a preview and the inferred schema (column names and types) after upload. |
| FR-04 | Accept a natural-language question about an uploaded dataset. |
| FR-05 | Produce a structured query plan, then SQL from the plan. Simple single-table questions skip the plan stage and go straight to SQL. Ask a clarifying question when the request is ambiguous. |
| FR-06 | Validate SQL through the AST validator before any execution. Show a clear reason when a query is rejected. |
| FR-07 | Execute validated SQL on a read-only role with a time limit and a row cap. Show a notice when results are truncated. |
| FR-08 | Show the SQL, the plan summary, and the result table for every answer. |
| FR-09 | Return a structured chart spec, validate it against the result columns, and render it with Apache ECharts. Fall back to the table when the spec is invalid. |
| FR-10 | Generate insights and recommendations from the (capped) result, never from the raw dataset. |
| FR-11 | Let the user assemble answers into a report and download it as PDF or HTML. |
| FR-12 | Provide an evaluation page that runs the golden question sets and reports accuracy, rejection rate, latency, and token cost. |
| FR-13 | Provide a "Delete my data now" action. |
| FR-14 | Offer sample datasets for instant try-out. |
| FR-15 | Delete all session data automatically 24 hours after creation. |

## 1.7 Non-functional requirements

| Area | Target |
| --- | --- |
| Security | No cross-session data access. No mutation possible through generated SQL. Zero validator bypasses in the adversarial suite. |
| Performance | p95 question-to-answer under 8 seconds on warm services. Upload of a 10 MB file under 15 seconds. |
| Privacy | Data deleted within 24 hours plus one cleanup cycle. Clear notice that question text, schema, and sample rows are sent to Google's Gemini API. |
| Reliability | Graceful behaviour on cold starts, Gemini quota errors, and database limits. Best-effort uptime. |
| Cost | Entirely within free tiers. Hard guards against quota exhaustion. |
| Observability | Structured logs with request IDs. Every pipeline stage timed and recorded. |
| Accessibility | Keyboard-navigable UI, sufficient contrast, chart data also available as a table. |
| Maintainability | File and function size limits enforced by lint. Tests mirror the source layout. |

## 1.8 Initial limits (defaults)

| Limit | Default |
| --- | --- |
| Upload size | 10 MB |
| Rows per sheet | 100,000 |
| Columns per sheet | 100 |
| Sheets per file | 5 |
| Datasets per session | 3 |
| Result rows returned | 1,000 |
| Query timeout | 10 seconds |
| Questions per session per hour | 30 |
| Session lifetime | 24 hours |

## 1.9 Success metrics

| Metric | Target |
| --- | --- |
| Golden-set execution accuracy | At least 80% (stretch target: 90%) |
| Validator adversarial suite | 100% of malicious queries blocked |
| p95 answer latency | Under 8 seconds |
| Chart spec validity rate | At least 95% without fallback |
| Test coverage on validator and ingestion | At least 90% |

## 1.10 Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Gemini free-tier quota is exhausted | Rate limits, caching of identical questions, quota guard with a friendly message |
| Cold starts on the free API host | Loading states, a lightweight health ping on page load |
| Free database is small (about 0.5 GB) | Upload limits, global storage guard, fast cleanup |
| Prompt injection through cell contents | Treat data as untrusted. Safety lives in the validator, not in the prompt. |
| Wrong but plausible answers | Show SQL and plan. Track accuracy in the eval page. |
| Free-tier terms change | Keep hosting behind configuration. Document a migration path. |

## 1.11 Resolved questions

- **Decided:** Insights are generated on demand, to save quota.
- **Decided:** The plan stage is skipped for simple single-table questions. Evaluation tracks accuracy on both paths so the rule can be revisited.
