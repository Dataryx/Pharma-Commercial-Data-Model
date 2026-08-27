# Architecture

## Medallion flow

1. **Generator** (`src/pcdm/generate`) emits immutable landing files.
2. **Load** (`pcdm load`) registers landing tables in DuckDB and runs Python MDM.
3. **dbt** builds bronze → silver → gold marts with tests.
4. **Streamlit** / notebook consume gold.

## Cross-cutting

- `mdm/` golden records, xref, match evaluation
- `dq/` quarantine, test failures, run history
- `sec/` reserved for RLS (`sec_user_territory_access` documented in BI specs)

## Portability

SQL is DuckDB-first; adapter-specific helpers belong in `transform/macros/`. Snowflake and Postgres profiles are committed under `transform/profiles/profiles.yml` for future validation.
