"""Dagster software-defined assets wrapping generate → load → dbt."""

from pathlib import Path

from dagster import Definitions, asset
from dagster_dbt import DbtCliResource, dbt_assets

ROOT = Path(__file__).resolve().parents[1]


@asset
def generate_demo_data():
    from pcdm.generate.pipeline import run_generate

    return str(run_generate(scale="demo", seed=42, root=ROOT))


@asset(deps=[generate_demo_data])
def load_landing():
    from pcdm.load import load_landing
    from pcdm.cli import WAREHOUSE

    load_landing(scale="demo", root=ROOT, warehouse=WAREHOUSE)
    return str(WAREHOUSE)


dbt_project = ROOT / "transform"


@dbt_assets(manifest=dbt_project / "target" / "manifest.json")
def pcdm_dbt_assets(context, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


defs = Definitions(
    assets=[generate_demo_data, load_landing],
    resources={
        "dbt": DbtCliResource(project_dir=str(dbt_project), profiles_dir=str(dbt_project / "profiles")),
    },
)
