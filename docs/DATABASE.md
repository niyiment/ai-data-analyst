# Database Design

## 6.1 Overview

One PostgreSQL database with three kinds of schema:

| Schema | Purpose | Lifetime |
| --- | --- | --- |
| `app` | Metadata: sessions, datasets, query history, reports | Rows deleted with their session |
| `ds_<random id>` | The user's uploaded tables, one schema per dataset | Dropped with the session |
| `demo_<name>` and `eval` | Sample datasets and evaluation data | Persistent, read-only |

User data never sits in `app`, and metadata never sits in a `ds_` schema.

## 6.2 Roles and privileges

| Role | Used by | Privileges |
| --- | --- | --- |
| `app_owner` | Migrations only | Owns all objects. Never used by the running API. |
| `app_rw` | API services (metadata and ingestion) | Read and write on `app`. Create and drop `ds_` schemas. Insert into `ds_` tables during ingestion. |
| `analyst_ro` | Query executor only | Usage and select on `ds_` and `demo_` schemas. **No access to `app`.** No create, no temp, no function creation. |

Execution rules for `analyst_ro`: every query runs inside a read-only transaction, with a local statement timeout, a locked `search_path` containing only the dataset's schema, and a row cap applied by wrapping the query. Grants on a new `ds_` schema are issued at creation time by the dataset service.

## 6.3 Metadata tables (schema `app`)

### `sessions`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `token_hash` | Text | Unique. Hash of the cookie token. The token itself is never stored. |
| `created_at` | Timestamp with time zone | |
| `expires_at` | Timestamp with time zone | `created_at` plus 24 hours. Indexed. |
| `status` | Text | `active`, `expired`, `deleted` |
| `ip_hash` | Text | Salted hash, used only for rate limiting |

### `datasets`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `session_id` | UUID | Foreign key to `sessions`, cascade delete. Indexed. |
| `schema_name` | Text | Unique. Server-generated, e.g. `ds_` plus 16 random lowercase hex characters. |
| `original_filename` | Text | Sanitised for display only. Never used in SQL. |
| `file_type` | Text | `csv` or `xlsx` |
| `size_bytes` | Integer | |
| `status` | Text | `processing`, `ready`, `failed` |
| `created_at`, `expires_at` | Timestamp with time zone | |

### `dataset_tables` (one per sheet or CSV)

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `dataset_id` | UUID | Foreign key, cascade delete |
| `table_name` | Text | Sanitised, unique within the dataset |
| `source_name` | Text | Original sheet name, for display |
| `row_count` | Integer | |

### `dataset_columns`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `table_id` | UUID | Foreign key, cascade delete |
| `ordinal` | Integer | Original column order |
| `original_name` | Text | As in the file, for display |
| `column_name` | Text | Sanitised `snake_case`, collision-safe |
| `pg_type` | Text | `text`, `bigint`, `double precision`, `boolean`, `date`, `timestamp` |
| `nullable` | Boolean | |
| `sample_values` | JSON | A few values, used for prompts. Deleted with the session. |
| `description` | Text | Optional user or AI-written description |

### `query_runs` (one per question)

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `session_id`, `dataset_id` | UUID | Foreign keys, cascade delete. Indexed together with `created_at`. |
| `question` | Text | |
| `plan` | JSON | The structured plan (nullable when skipped for simple single-table questions) |
| `generated_sql` | Text | |
| `validation_status` | Text | `accepted` or `rejected` |
| `rejection_reasons` | JSON | Rule names and messages |
| `status` | Text | `succeeded`, `rejected`, `failed`, `needs_clarification` |
| `error_code` | Text | Stable machine-readable code |
| `row_count` | Integer | Rows returned |
| `truncated` | Boolean | |
| `stage_timings_ms` | JSON | Plan, generate, validate, execute, chart, insights |
| `tokens_in`, `tokens_out` | Integer | For cost tracking |
| `created_at` | Timestamp with time zone | |

### `query_artifacts` (chart spec and insights for a run)

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `query_run_id` | UUID | Foreign key, cascade delete |
| `kind` | Text | `chart_spec` or `insights` |
| `content` | JSON | Validated payload |
| `is_valid` | Boolean | Chart specs that failed validation are recorded as invalid |

### `reports` and `report_items`

- `reports` holds `id`, `session_id` (cascade), `title`, `created_at`.
- `report_items` holds `id`, `report_id` (cascade), `query_run_id`, `position`, and an optional `note`.

Result rows are **not** stored. Re-running a query regenerates them, which keeps stored data small and short-lived.

## 6.4 Evaluation data

Golden sets (questions, reference SQL, category, difficulty, `order_sensitive`, `expects_clarification`) live in version control as validated JSON under `api/src/app/evaluation/golden/`, not in database tables.

| Table | Key columns |
| --- | --- |
| `app.eval_runs` (migration `0004`) | `id`, `set_name`, `model` (`provider:model`), `prompt_version`, `started_at`, `finished_at`, `accuracy`, `detail` (JSON: aggregate metrics and per-question results with `outcome` `correct`/`wrong`/`rejected`/`error`, `generated_sql`, `latency_ms`, `failure_category`) |

Demo datasets live in persistent `demo_<name>` schemas created by migration, with `USAGE`/`SELECT` granted to `analyst_ro`:

| Schema | Tables | Created by |
| --- | --- | --- |
| `demo_retail_sales` | `retail_sales` (40 orders, Jan–Mar 2026), `regions` (manager, revenue target) | migration `0005` (frozen seed data; change only via a new migration) |

Evaluation data holds no user data and is never touched by cleanup.

## 6.5 Identifier handling

- Schema names are generated by the server, never derived from user input.
- Table and column names are produced by one sanitiser: lowercase, replace non-alphanumerics with underscores, prefix names that start with a digit, truncate to the PostgreSQL limit, de-duplicate with numeric suffixes, and avoid reserved words.
- The sanitiser keeps the original-to-sanitised mapping in `dataset_columns` so the model prompt and the UI can use friendly names.
- All dynamic identifiers are quoted using the driver's identifier API.

## 6.6 Type inference

Sample the column, then pick the narrowest type that fits every non-null value: `boolean`, `bigint`, `double precision`, `date`, `timestamp`, otherwise `text`. Mixed or ambiguous columns become `text`. Treat common null markers (empty string, `NA`, `N/A`, `null`) as null. The user may override a type on the schema review screen before any querying.

## 6.7 Indexes

- `sessions(token_hash)` unique
- `sessions(expires_at)`
- `datasets(session_id)`
- `datasets(schema_name)` unique
- `query_runs(session_id, created_at)`
- `dataset_tables(dataset_id)`
- `dataset_columns(table_id, ordinal)`

User tables get no indexes in the MVP.

## 6.8 Retention and cleanup

1. Find sessions where `expires_at` is in the past.
2. For each, drop every `ds_` schema it owns (idempotent, `IF EXISTS`).
3. Delete the session row. Cascades remove all dependent metadata.
4. Record counts for observability. No personal data in the log.

The same routine serves "Delete my data now" and lazy expiry on access.

## 6.9 Capacity guard

The free database is small. Before accepting an upload, check total used storage against a threshold and the number of active sessions. If over, return a friendly "try again shortly" message. Cleanup also runs on a frequent schedule.

## 6.10 Migrations

Use Alembic. One migration per change, reversible, reviewed with the `add-db-migration` skill. Migrations run with `app_owner` in CI or at deploy time, never from the running API.
