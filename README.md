# Pharma Commercial Data Model (PCDM)

Reference implementation of a manufacturer commercial analytics warehouse.

It covers the messy parts teams usually discover too late: projected retail
demand (Xponent-*style*, not proprietary), wholesaler 867 sales-out, specialty
pharmacy funnel data, HCP/HCO match-merge, territory alignment restatement, and
metric definitions that are actually tested.

Everything is synthetic. Same seed → same files. No cloud account required.

## Layout

```text
apps/commercial_insights/   Streamlit demo for analysts
data/                       Generated landing files (demo scale can be committed)
dbt/                        Medallion transforms (bronze → silver → mdm → gold)
docs/                       Architecture, metrics, ERDs, runbooks
ops/scripts/                Warehouse DDL and small utilities
ops/orchestration/          Optional Dagster entrypoint
src/pcdm/                   Generator, EDI parser, MDM, CLI
tests/                      Pytest + golden metric fixtures
warehouse/                  Local DuckDB file (gitignored)
```

## Quick start

```bash
python -m pip install -e ".[dev]"
python -m pcdm all --scale demo --seed 42
python -m streamlit run apps/commercial_insights/Home.py
```

On Unix / Git Bash you can also use `make setup && make all`.

Warehouse path: `warehouse/pcdm.duckdb`.

## What this is good for

- Answering TRx / NRx / share questions nationally and by territory
- Seeing where specialty patients fall out of the funnel
- Reconciling retail demand against 867 and SP dispenses
- Showing IC the difference between as-reported and current alignment
- Proving MDM quality against known synthetic duplicates / false friends

## Important domain notes

- Demand, shipments, and specialty fills are related but not the same thing
- Projected demand is decimal on purpose; do not cast TRx to int
- NBRx needs patient history — we only compute it where specialty data exists
- NPI is useful but not a safe primary key for HCPs
- Patient cells under `MIN_CELL_SIZE` are suppressed, not zeroed

## Docs

Start with [docs/architecture.md](docs/architecture.md) and
[docs/runbook.md](docs/runbook.md). Metric definitions live in
[docs/metrics/metric-definitions.md](docs/metrics/metric-definitions.md).

## License

MIT — intended as a teaching / reference codebase, not a production feed of
licensed vendor data.
