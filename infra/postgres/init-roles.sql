-- Local PostgreSQL bootstrap: creates least-privilege roles and base schemas.
-- Matches docs/DATABASE.md section 6.1 and 6.2.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') THEN
        CREATE ROLE app_rw LOGIN PASSWORD 'local_app_rw_password';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analyst_ro') THEN
        CREATE ROLE analyst_ro LOGIN PASSWORD 'local_analyst_ro_password';
    END IF;
END
$$;

CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION app_owner;
CREATE SCHEMA IF NOT EXISTS eval AUTHORIZATION app_owner;

-- app_rw: read/write on app schema, create schemas for ds_* datasets
GRANT USAGE ON SCHEMA app TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO app_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA app
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_rw;
GRANT CREATE ON DATABASE ai_data_analyst TO app_rw;

-- analyst_ro: no access to app schema, no create, no temp
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON DATABASE ai_data_analyst FROM analyst_ro;
REVOKE TEMP ON DATABASE ai_data_analyst FROM analyst_ro;
GRANT USAGE ON SCHEMA eval TO analyst_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA eval TO analyst_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA eval
    GRANT SELECT ON TABLES TO analyst_ro;
