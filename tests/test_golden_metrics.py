"""Golden metric regression fixture."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
WH = ROOT / "warehouse" / "pcdm.duckdb"
GOLDEN = ROOT / "tests" / "golden" / "metrics.csv"


@pytest.fixture(scope="module")
def metrics() -> dict[str, float]:
    if not WH.exists():
        pytest.skip("warehouse not built")
    con = duckdb.connect(str(WH), read_only=True)
    brand_trx = con.execute(
        "select sum(brand_trx) from main_gold.mart_brand_performance_weekly"
    ).fetchone()[0]
    avg_share = con.execute(
        "select avg(trx_share) from main_gold.mart_brand_performance_weekly where trx_share is not null"
    ).fetchone()[0]
    precision = con.execute("select precision from main_mdm.mdm_match_evaluation").fetchone()[0]
    recall = con.execute("select recall from main_mdm.mdm_match_evaluation").fetchone()[0]
    funnel = con.execute("select n_referral, n_first_ship from main_gold.mart_specialty_funnel").fetchone()
    con.close()
    return {
        "brand_trx_total": float(brand_trx or 0),
        "avg_trx_share": float(avg_share or 0),
        "mdm_precision": float(precision or 0),
        "mdm_recall": float(recall or 0),
        "funnel_referrals": float(funnel[0] or 0),
        "funnel_first_ship": float(funnel[1] or 0),
    }


def test_golden_metrics_match_fixture(metrics):
    if not GOLDEN.exists():
        pytest.skip("golden file missing")
    golden = pd.read_csv(GOLDEN)
    if golden.iloc[0]["metric"] == "placeholder":
        # first run seeds golden
        rows = [{"metric": k, "value": v, "notes": "demo seed 42"} for k, v in metrics.items()]
        pd.DataFrame(rows).to_csv(GOLDEN, index=False)
        return
    gmap = dict(zip(golden["metric"], golden["value"].astype(float)))
    for k, v in metrics.items():
        assert k in gmap, f"missing golden key {k}"
        assert abs(gmap[k] - v) < max(1e-6, abs(gmap[k]) * 0.001), f"{k}: expected {gmap[k]} got {v}"
