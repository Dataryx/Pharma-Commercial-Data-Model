# ADR 0001 — Choose DuckDB for local/CI

## Context

Need zero-setup CI and laptop reproducibility without warehouse credentials.

## Decision

DuckDB as default storage/compute; Snowflake/Postgres profiles committed for portability proofs.

## Consequences

Fast CI; some SQL dialect differences isolated in macros.

## Alternatives

SQLite (weaker analytics), local Postgres (heavier setup).
