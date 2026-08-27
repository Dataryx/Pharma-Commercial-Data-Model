-- Local DuckDB bootstrap.
-- Keeps medallion schemas plus MDM / DQ / security side schemas in one place.

CREATE SCHEMA IF NOT EXISTS landing;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS mdm;
CREATE SCHEMA IF NOT EXISTS dq;
CREATE SCHEMA IF NOT EXISTS semantic;
CREATE SCHEMA IF NOT EXISTS sec;

-- Lightweight run log so we can see what loaded when
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
