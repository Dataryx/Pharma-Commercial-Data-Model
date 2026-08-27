# Architecture

## Flow

1. `pcdm generate` writes immutable landing files under `data/<scale>/landing`
2. `pcdm load` registers those files in DuckDB and runs HCP MDM in Python
3. `dbt/` builds bronze → silver → gold marts (plus mdm publish models)
4. `apps/commercial_insights` and notebooks read from gold

## Why the folder names

| Folder | Role |
|---|---|
| `data/` | What arrived (synthetic stand-ins for vendor drops) |
| `dbt/` | How we transform it |
| `src/pcdm/` | Generator, parser, matcher, CLI |
| `apps/` | Human-facing demos |
| `ops/` | DDL, orchestration stubs, one-off scripts |

## Portability

Local/CI runs on DuckDB. Snowflake and Postgres profile stubs sit in
`dbt/profiles/profiles.yml` for later adapter checks. Anything dialect-specific
should go behind a macro under `dbt/macros/`.
