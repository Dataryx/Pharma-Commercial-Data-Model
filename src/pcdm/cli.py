"""PCDM command-line interface."""

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
DATASETS = ROOT / "datasets"


@click.group()
@click.version_option(__version__)
def main() -> None:
    """Pharma Commercial Data Model CLI."""


@main.command("init-db")
def init_db() -> None:
    """Create DuckDB warehouse and schemas."""
    WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)
    sql = (ROOT / "scripts" / "database.sql").read_text(encoding="utf-8")
    con = duckdb.connect(str(WAREHOUSE))
    con.execute(sql)
    con.close()
    click.echo(f"Initialized warehouse at {WAREHOUSE}")


@main.command("generate")
@click.option("--scale", type=click.Choice(["demo", "small", "large"]), default="demo")
@click.option("--seed", type=int, default=42)
def generate(scale: str, seed: int) -> None:
    """Generate synthetic landing + ground-truth datasets."""
    from pcdm.generate.pipeline import run_generate

    out = run_generate(scale=scale, seed=seed, root=ROOT)
    click.echo(f"Generated {scale} dataset at {out}")


@main.command("load")
@click.option("--scale", type=click.Choice(["demo", "small", "large"]), default="demo")
def load(scale: str) -> None:
    """Load landing files into DuckDB landing/bronze raw tables."""
    from pcdm.load import load_landing

    load_landing(scale=scale, root=ROOT, warehouse=WAREHOUSE)
    click.echo(f"Loaded landing for scale={scale}")


@main.command("clean")
@click.option("--scale", type=click.Choice(["demo", "small", "large", "all"]), default="demo")
def clean(scale: str) -> None:
    """Remove generated datasets (except committed demo source if scale!=demo wipe)."""
    if scale == "all":
        for s in ("small", "large"):
            p = DATASETS / s
            if p.exists():
                shutil.rmtree(p)
    else:
        p = DATASETS / scale
        if scale != "demo" and p.exists():
            shutil.rmtree(p)
        land = DATASETS / scale / "landing"
        if land.exists() and scale == "demo":
            # keep demo committed files; wipe runtime quarantine only
            q = land / "quarantine"
            if q.exists():
                shutil.rmtree(q)
    if WAREHOUSE.exists():
        WAREHOUSE.unlink()
    click.echo("Clean complete")


@main.command("docs-generate")
def docs_generate() -> None:
    """Generate data dictionary and ERD mermaid from dbt manifest when present."""
    from pcdm.docs_tools import generate_data_dictionary, generate_erd

    generate_data_dictionary(ROOT)
    generate_erd(ROOT)
    click.echo("Docs artifacts generated")


@main.command("erd")
def erd() -> None:
    """Regenerate ERD from dbt manifest."""
    from pcdm.docs_tools import generate_erd

    generate_erd(ROOT)
    click.echo("ERD regenerated")


@main.command("checksum")
@click.option("--scale", default="demo")
def checksum(scale: str) -> None:
    """Print SHA256 checksums of landing files."""
    base = DATASETS / scale / "landing"
    if not base.exists():
        raise click.ClickException(f"Missing {base}")
    manifest: dict[str, str] = {}
    for path in sorted(base.rglob("*")):
        if path.is_file() and "quarantine" not in path.parts:
            h = hashlib.sha256(path.read_bytes()).hexdigest()
            rel = str(path.relative_to(base)).replace("\\", "/")
            manifest[rel] = h
            click.echo(f"{h}  {rel}")
    out = DATASETS / scale / "checksums.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _dbt_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PCDM_DUCKDB_PATH"] = str(WAREHOUSE.resolve())
    return env


@main.command("all")
@click.option("--scale", default="demo")
@click.option("--seed", default=42)
def all_cmd(scale: str, seed: int) -> None:
    """Run generate → load → dbt build → pytest."""
    ctx = click.get_current_context()
    ctx.invoke(init_db)
    ctx.invoke(generate, scale=scale, seed=seed)
    ctx.invoke(load, scale=scale)
    env = _dbt_env()
    subprocess.check_call(
        ["dbt", "deps", "--project-dir", str(ROOT / "transform"),
         "--profiles-dir", str(ROOT / "transform" / "profiles")],
        env=env,
    )
    subprocess.check_call(
        ["dbt", "build", "--project-dir", str(ROOT / "transform"),
         "--profiles-dir", str(ROOT / "transform" / "profiles"), "--target", "duckdb"],
        env=env,
    )
    subprocess.check_call([sys.executable, "-m", "pytest", str(ROOT / "tests"), "-q"])
    click.echo("pcdm all complete")


if __name__ == "__main__":
    raise SystemExit(main())
