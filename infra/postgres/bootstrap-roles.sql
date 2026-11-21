-- Production role bootstrap (Neon or any managed PostgreSQL). Idempotent; run before
-- migrations by .github/workflows/cd.yml as the database owner (DATABASE_URL_OWNER).
-- Local development uses init-roles.sql instead (fixed local-only passwords).
--
-- Required psql variables (passed from GitHub secrets, never committed):
--   psql -v app_rw_password=... -v analyst_ro_password=... -f bootstrap-roles.sql
-- psql variables are not expanded inside DO blocks, so dynamic SQL uses \gexec.

\set ON_ERROR_STOP on

SELECT 'CREATE ROLE app_rw LOGIN'
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') \gexec
SELECT 'CREATE ROLE analyst_ro LOGIN'
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analyst_ro') \gexec

ALTER ROLE app_rw WITH LOGIN PASSWORD :'app_rw_password';
ALTER ROLE analyst_ro WITH LOGIN PASSWORD :'analyst_ro_password';

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS eval;

-- app_rw: read/write on app, create per-dataset ds_* schemas.
GRANT USAGE ON SCHEMA app TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO app_rw;
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA app '
    'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_rw', current_user) \gexec
SELECT format('GRANT CREATE ON DATABASE %I TO app_rw', current_database()) \gexec

-- analyst_ro: no access to app, no create, no temp; read-only on eval and demo_* schemas
-- (demo grants are issued by migrations).
REVOKE ALL ON SCHEMA public FROM PUBLIC;
SELECT format('REVOKE CREATE ON DATABASE %I FROM analyst_ro', current_database()) \gexec
SELECT format('REVOKE TEMP ON DATABASE %I FROM analyst_ro', current_database()) \gexec
GRANT USAGE ON SCHEMA eval TO analyst_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA eval TO analyst_ro;
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA eval GRANT SELECT ON TABLES TO analyst_ro',
    current_user) \gexec
