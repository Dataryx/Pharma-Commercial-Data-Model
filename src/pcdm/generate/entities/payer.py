"""Payers, plans, formulary status."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from pcdm.generate.config import ScaleProfile
from pcdm.generate.entities.product import ProductBundle


PLAN_TYPES = ["COMM", "MCARE_D", "MCAID", "CASH"]


@dataclass
class PayerBundle:
    payers: pd.DataFrame
    plans: pd.DataFrame
    formulary: pd.DataFrame


def generate_payers(rng: np.random.Generator, profile: ScaleProfile, products: ProductBundle) -> PayerBundle:
    payers = pd.DataFrame(
        [
            {"payer_id": f"PAY{i:03d}", "payer_name": name}
            for i, name in enumerate(
                ["SynthoHealth", "UnionCare", "Prairie Mutual", "CoastalRx", "Metro Benefit"]
            )
        ]
    )
    plans = []
    for i, p in payers.iterrows():
        for pt in PLAN_TYPES:
            plans.append(
                {
                    "plan_id": f"{p['payer_id']}_{pt}",
                    "payer_id": p["payer_id"],
                    "plan_name": f"{p['payer_name']} {pt}",
                    "plan_type": pt,
                    "lives": int(rng.integers(50_000, 2_000_000)),
                }
            )
    plans_df = pd.DataFrame(plans)
    start = date(2024, 1, 1)
    form_rows = []
    brand_products = products.products["product_id"].tolist()
    for _, plan in plans_df.iterrows():
        for pid in brand_products:
            tier = int(rng.integers(1, 4))
            pa = rng.random() < (0.4 if plan["plan_type"] == "MCARE_D" else 0.2)
            form_rows.append(
                {
                    "plan_id": plan["plan_id"],
                    "product_id": pid,
                    "tier": tier,
                    "pa_required": pa,
                    "step_edit": rng.random() < 0.1,
                    "ql_flag": rng.random() < 0.15,
                    "valid_from": start.isoformat(),
                    "valid_to": (start + timedelta(days=180)).isoformat(),
                    "is_current": False,
                }
            )
            # mid-year change
            form_rows.append(
                {
                    "plan_id": plan["plan_id"],
                    "product_id": pid,
                    "tier": max(1, tier - 1) if rng.random() < 0.3 else tier,
                    "pa_required": pa and rng.random() < 0.7,
                    "step_edit": False,
                    "ql_flag": rng.random() < 0.1,
                    "valid_from": (start + timedelta(days=180)).isoformat(),
                    "valid_to": "9999-12-31",
                    "is_current": True,
                }
            )
    return PayerBundle(payers=payers, plans=plans_df, formulary=pd.DataFrame(form_rows))
