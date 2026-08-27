"""
Dagster wiring for the local demo pipeline.

Keep this thin — assets just call the same functions the CLI uses so we don't
end up with two sources of truth for generate/load.
"""

from pathlib import Path

from dagster import Definitions, asset
from dagster_dbt import DbtCliResource, dbt_assets

# ops/orchestration -> repo root
ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT = ROOT / "dbt"


@asset
def generate_demo_data():
    from pcdm.generate.pipeline import run_generate

    return str(run_generate(scale="demo", seed=42, root=ROOT))


@asset(deps=[generate_demo_data])
def load_landing_asset():
    from pcdm.cli import WAREHOUSE
    from pcdm.load import load_landing

    load_landing(scale="demo", root=ROOT, warehouse=WAREHOUSE)
    return str(WAREHOUSE)


@dbt_assets(manifest=DBT_PROJECT / "target" / "manifest.json")
def pcdm_dbt_assets(context, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


defs = Definitions(
    assets=[generate_demo_data, load_landing_asset],
    resources={
        "dbt": DbtCliResource(
            project_dir=str(DBT_PROJECT),
            profiles_dir=str(DBT_PROJECT / "profiles"),
        ),
    },
)
