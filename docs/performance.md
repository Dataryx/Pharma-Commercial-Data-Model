# Performance (demo profile)

| Step | Duration (approx) |
|---|---|
| `pcdm generate --scale demo` | ~15s |
| `pcdm load` | ~25s |
| `dbt build` | ~7s |
| `pytest` | ~60s |

Large profile (250k HCP) is intended for offline benchmarking; not run in CI.
