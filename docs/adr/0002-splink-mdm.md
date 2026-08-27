# ADR 0002 — MDM engine

## Context

Need deterministic + probabilistic HCP match-merge with measurable precision/recall.

## Decision

Custom blocking/scoring with NetworkX clustering and Fellegi–Sunter-style weights in `src/pcdm/mdm`. Splink remains an optional upgrade path (dependency weight vs DuckDB integration complexity).

## Consequences

Full control in CI; document Splink as future enhancement in open-questions.

## Alternatives

Splink-only, recordlinkage-only.
