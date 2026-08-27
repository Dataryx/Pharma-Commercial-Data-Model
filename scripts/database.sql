-- PCDM warehouse bootstrap (DuckDB / portable DDL)
-- Schemas follow medallion + cross-cutting MDM/DQ layers.

CREATE SCHEMA IF NOT EXISTS landing;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS mdm;
CREATE SCHEMA IF NOT EXISTS dq;
CREATE SCHEMA IF NOT EXISTS semantic;
CREATE SCHEMA IF NOT EXISTS sec;

-- Run history / observability stubs
CREATE TABLE IF NOT EXISTS dq.run_history (
    run_id VARCHAR PRIMARY KEY,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    scale VARCHAR,
    seed INTEGER,
    status VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS dq.test_results (
    test_id VARCHAR,
    run_id VARCHAR,
    model_name VARCHAR,
    test_name VARCHAR,
    status VARCHAR,
    failed_row_count BIGINT,
    recorded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dq.quarantine_manifest (
    quarantine_id VARCHAR PRIMARY KEY,
    source_system VARCHAR,
    source_file VARCHAR,
    reason VARCHAR,
    row_count BIGINT,
    quarantined_at TIMESTAMP,
    batch_id VARCHAR
);
