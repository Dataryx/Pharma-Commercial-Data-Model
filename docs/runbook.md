# Runbook

## Fresh machine

```bash
python -m pip install -e ".[dev]"
python -m pcdm all --scale demo --seed 42
python -m streamlit run apps/commercial_insights/Home.py
```

## Day-to-day

| Task | Command |
|---|---|
| Regen synthetic data | `python -m pcdm generate --scale demo --seed 42` |
| Reload DuckDB | `python -m pcdm load --scale demo` |
| Rebuild models/tests | `cd dbt && dbt build --profiles-dir profiles --target duckdb` |
| Open insights app | `python -m streamlit run apps/commercial_insights/Home.py` |

Set `PCDM_DUCKDB_PATH` to an absolute path if dbt can't find the warehouse
(Windows relative paths from `dbt/` are unreliable).

## Adding a source

1. Emit files from `src/pcdm/generate/emitters/`
2. Register them in `src/pcdm/load.py`
3. Add a `br_*` model under `dbt/models/bronze/`
4. Document quirks in `docs/sources/`

## Adding a metric

1. Write the definition in `docs/metrics/metric-definitions.md`
2. Put the logic in a gold mart (or a shared macro)
3. Add a dbt test for the invariant in the same change
4. Refresh `tests/golden/metrics.csv` after a known-good demo build
