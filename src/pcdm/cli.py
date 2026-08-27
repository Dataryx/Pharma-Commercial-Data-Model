"""
PCDM CLI.

Thin wrappers around generate → load → dbt → tests. Most of the real work lives
in the Python package and the dbt project under dbt/.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import click
import duckdb

from pcdm import __version__

ROOT = Path(__file__).resolve().parents[2]
WAREHOUSE = ROOT / "warehouse" / "pcdm.duckdb"
DATA_ROOT = ROOT / "data"
DBT_PROJECT = ROOT / "dbt"
SCHEMA_SQL = ROOT / "ops" / "scripts" / "database.sql"


@click.group()
@click.version_option(__version__)
def main() -> None:
    """Pharma commercial data model — local warehouse toolkit."""


@main.command("init-db")
def init_db() -> None:
    """Create the DuckDB file and empty schemas if they are missing."""
    WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    con = duckdb.connect(str(WAREHOUSE))
    con.execute(sql)
    con.close()
    click.echo(f"Warehouse ready: {WAREHOUSE}")


@main.command("generate")
@click.option("--scale", type=click.Choice(["demo", "small", "large"]), default="demo")
@click.option("--seed", type=int, default=42)
def generate(scale: str, seed: int) -> None:
    """Build synthetic landing files. Same seed should always give the same bytes."""
    from pcdm.generate.pipeline import run_generate

    out = run_generate(scale=scale, seed=seed, root=ROOT)
    click.echo(f"Wrote {scale} data under {out}")


@main.command("load")
@click.option("--scale", type=click.Choice(["demo", "small", "large"]), default="demo")
def load(scale: str) -> None:
    """Register landing files in DuckDB and run HCP match-merge."""
    from pcdm.load import load_landing

    load_landing(scale=scale, root=ROOT, warehouse=WAREHOUSE)
    click.echo(f"Load finished for scale={scale}")


@main.command("clean")
@click.option("--scale", type=click.Choice(["demo", "small", "large", "all"]), default="demo")
def clean(scale: str) -> None:
    """Drop generated scales / warehouse. Demo source files are left alone."""
    if scale == "all":
        for s in ("small", "large"):
            p = DATA_ROOT / s
            if p.exists():
                shutil.rmtree(p)
    else:
        p = DATA_ROOT / scale
        if scale != "demo" and p.exists():
            shutil.rmtree(p)
        land = DATA_ROOT / scale / "landing"
        if land.exists() and scale == "demo":
            q = land / "quarantine"
            if q.exists():
                shutil.rmtree(q)
    if WAREHOUSE.exists():
        WAREHOUSE.unlink()
    click.echo("Clean complete")


@main.command("docs-generate")
def docs_generate() -> None:
    """Rebuild data dictionary + ERD stubs from the dbt manifest when it exists."""
    from pcdm.documentation import generate_data_dictionary, generate_erd

    generate_data_dictionary(ROOT)
    generate_erd(ROOT)
    click.echo("Docs artifacts updated")


@main.command("erd")
def erd() -> None:
    """Refresh Mermaid ERD from dbt."""
    from pcdm.documentation import generate_erd

    generate_erd(ROOT)
    click.echo("ERD regenerated")


@main.command("checksum")
@click.option("--scale", default="demo")
def checksum(scale: str) -> None:
    """Hash every landing file so we can prove seed reproducibility."""
    base = DATA_ROOT / scale / "landing"
    if not base.exists():
        raise click.ClickException(f"Missing {base}")
    manifest: dict[str, str] = {}
    for path in sorted(base.rglob("*")):
        if path.is_file() and "quarantine" not in path.parts:
            h = hashlib.sha256(path.read_bytes()).hexdigest()
            rel = str(path.relative_to(base)).replace("\\", "/")
            manifest[rel] = h
            click.echo(f"{h}  {rel}")
    out = DATA_ROOT / scale / "checksums.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _dbt_env() -> dict[str, str]:
    # Absolute path avoids Windows relative-path weirdness when cwd is dbt/
    env = os.environ.copy()
    env["PCDM_DUCKDB_PATH"] = str(WAREHOUSE.resolve())
    return env


@main.command("all")
@click.option("--scale", default="demo")
@click.option("--seed", default=42)
def all_cmd(scale: str, seed: int) -> None:
    """One-shot: generate, load, dbt build, pytest."""
    ctx = click.get_current_context()
    ctx.invoke(init_db)
    ctx.invoke(generate, scale=scale, seed=seed)
    ctx.invoke(load, scale=scale)
    env = _dbt_env()
    subprocess.check_call(
        [
            "dbt",
            "deps",
            "--project-dir",
            str(DBT_PROJECT),
            "--profiles-dir",
            str(DBT_PROJECT / "profiles"),
        ],
        env=env,
    )
    subprocess.check_call(
        [
            "dbt",
            "build",
            "--project-dir",
            str(DBT_PROJECT),
            "--profiles-dir",
            str(DBT_PROJECT / "profiles"),
            "--target",
            "duckdb",
        ],
        env=env,
    )
    subprocess.check_call([sys.executable, "-m", "pytest", str(ROOT / "tests"), "-q"])
    click.echo("pcdm all complete")


if __name__ == "__main__":
    raise SystemExit(main())
