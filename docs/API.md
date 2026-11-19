# API Contract (Overview)

Base path: `/api/v1`. JSON everywhere except uploads (`multipart/form-data`) and report downloads. Session identity comes only from the cookie.

## Endpoints

| Method and path | Purpose | Notes |
| --- | --- | --- |
| `GET /health` | Liveness and warm-up | No auth |
| `POST /sessions` | Start a session (also done implicitly) | Sets cookie |
| `GET /sessions/me` | Session status and expiry time | |
| `DELETE /sessions/me` | Delete my data now | Runs the cleanup routine |
| `POST /datasets` | Upload a file | Multipart. Returns dataset with tables and columns. |
| `POST /datasets/samples/{name}` | Load a sample dataset | |
| `GET /datasets` | List my datasets | |
| `GET /datasets/{id}` | Schema, preview rows | Ownership checked |
| `PATCH /datasets/{id}/columns/{column_id}` | Rename a column or override a type | |
| `DELETE /datasets/{id}` | Delete one dataset | |
| `POST /datasets/{id}/queries` | Ask a question | Returns plan, SQL, result, chart spec; or a clarification request |
| `POST /queries/{id}/insights` | Generate insights on demand | |
| `GET /datasets/{id}/queries` | Question history | Paginated |
| `POST /reports` | Create a report from query runs | |
| `GET /reports/{id}/export?format=pdf` | Download report | `pdf` or `html` |
| `POST /eval/runs` | Start an evaluation | Rate limited |
| `GET /eval/runs/{id}` | Progress and results | |
| `POST /internal/cleanup` | Scheduled cleanup | Secret header. Not exposed to the browser. |

## Error shape

Every error response is a JSON object with:

- `code`
- `message`
- `details`
- `request_id`

Stable codes include: `SESSION_EXPIRED`, `FILE_TOO_LARGE`, `UNSUPPORTED_FILE`, `QUERY_REJECTED`, `QUERY_TIMEOUT`, `QUOTA_EXCEEDED`, `RATE_LIMITED`, `NEEDS_CLARIFICATION`, `NOT_FOUND`.

## Ownership rule

Every endpoint that takes an ID resolves it through the current session. A resource belonging to another session returns the same response as a missing one (`NOT_FOUND`).
