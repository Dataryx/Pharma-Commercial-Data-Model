"""
DuckDB helpers for the Streamlit insights app.

dbt-duckdb prefixes custom schemas (gold -> main_gold), so we centralize that
mapping here instead of hard-coding it on every page.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

# apps/commercial_insights/db.py -> repo root
ROOT = Path(__file__).resolve().parents[2]
WAREHOUSE = ROOT / "warehouse" / "pcdm.duckdb"

SCHEMA = {
    "gold": "main_gold",
    "mdm": "main_mdm",
    "silver": "main_silver",
    "bronze": "main_bronze",
}


def connect() -> duckdb.DuckDBPyConnection:
    if not WAREHOUSE.exists():
        raise FileNotFoundError(
            f"Warehouse not found at {WAREHOUSE}. "
            "From the repo root run: python -m pcdm all --scale demo"
        )
    return duckdb.connect(str(WAREHOUSE), read_only=True)


def t(layer: str, name: str) -> str:
    """Return a fully qualified table name for the local DuckDB file."""
    return f"{SCHEMA.get(layer, layer)}.{name}"
