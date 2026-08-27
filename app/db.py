"""Shared DuckDB connection helpers for the Streamlit demo."""

from __future__ import annotations

from pathlib import Path

import duckdb

# app/db.py -> project root
ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "warehouse" / "pcdm.duckdb"

# dbt-duckdb custom schemas land as main_<schema>
SCHEMA = {
    "gold": "main_gold",
    "mdm": "main_mdm",
    "silver": "main_silver",
    "bronze": "main_bronze",
}


def connect() -> duckdb.DuckDBPyConnection:
    if not WAREHOUSE.exists():
        raise FileNotFoundError(
            f"Warehouse not found at {WAREHOUSE}. Run `python -m pcdm all --scale demo` first."
        )
    return duckdb.connect(str(WAREHOUSE), read_only=True)


def t(layer: str, name: str) -> str:
    """Qualify a model name with the physical DuckDB schema."""
    return f"{SCHEMA.get(layer, layer)}.{name}"
