# Security and Threat Model

## Threats and mitigations

| Threat | Mitigation |
| --- | --- |
| Model produces harmful SQL (mutation, exfiltration, resource abuse) | AST validation, function and table allowlists, read-only role and transaction, timeout, row cap |
| Prompt injection through cell values or column names | Treat sampled data as untrusted. Never grant the model tools. Safety enforced by validator and database, not by instructions. |
| Cross-session data access | Server-generated schema names, ownership resolved through the session, `analyst_ro` locked to one schema via `search_path`, schema-qualified allowlist |
| Session theft or fixation | Opaque random tokens, hashed at rest, `Secure` and `HttpOnly` cookie, rotation on creation, short lifetime |
| CSRF | `SameSite` cookies plus a CSRF token on state-changing requests, same-origin proxy |
| XSS | No raw HTML rendering of data or model text. Escape everything. Content Security Policy headers. |
| Spreadsheet formula injection | Neutralise leading `=`, `+`, `-`, `@` in exported reports and CSV |
| Malicious or oversized files | Size, row, column, and sheet limits. Parse with safe libraries. Reject archives that expand beyond limits. Content-type and extension checks. |
| Denial of service and cost abuse | Per-IP and per-session rate limits, global quota guard, concurrency cap on queries and uploads |
| Secrets leakage | Environment variables only, never in the repo or logs. Separate keys per environment. |
| Personal data sent to a third party | Visible privacy notice, minimal prompt content (schema plus a few sample rows), no full-dataset transfer, option to disable sample values |
| Data lingering after expiry | Two-layer cleanup, idempotent purge, verified by a scheduled test |

## Security tests

- An adversarial SQL suite (stacked statements, comments, CTE-wrapped mutations, `pg_` functions, catalog access, case and unicode tricks).
- An authorisation test that tries every endpoint with another session's IDs.
- An upload fuzz set.
