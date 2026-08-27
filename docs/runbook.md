# Runbook

## Fresh clone

1. `python -m pip install -e ".[dev]"`
2. `python -m pcdm init-db`
3. `python -m pcdm generate --scale demo --seed 42`
4. `python -m pcdm load --scale demo`
5. `cd transform && dbt deps --profiles-dir profiles && dbt build --profiles-dir profiles --target duckdb`
6. `python -m streamlit run app/Home.py`

## Backfill

Re-run `pcdm generate` (same seed for identical data) then `pcdm load` and `dbt build`. Late 867 files are represented via `delivery_delay_days` and quarantine folder for failed EDI.

## Add a source

1. Extend generator emitter
2. Register in `src/pcdm/load.py`
3. Add `br_*` model + tests
4. Document under `docs/sources/`

## Add a metric

1. Define in `docs/metrics/metric-definitions.md`
2. Add semantic measure/metric or mart column
3. Add dbt test for the invariant
4. Update golden fixture `tests/golden/metrics.csv` when stable
