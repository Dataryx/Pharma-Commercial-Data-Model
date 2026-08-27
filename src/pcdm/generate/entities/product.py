"""Products, NDCs, WAC history, market basket membership."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from pcdm.generate.config import BRAND_NAME, MARKET_ID, ScaleProfile


@dataclass
class ProductBundle:
    products: pd.DataFrame
    presentations: pd.DataFrame
    wac_history: pd.DataFrame
    market_membership: pd.DataFrame


def generate_products(rng: np.random.Generator, profile: ScaleProfile) -> ProductBundle:
    start = date(2024, 1, 1)
    # brand + 6 competitors; one mid-timeline launch; one basket switch
    names = [
        (BRAND_NAME, True, start, None),
        ("COMPARA", False, start, None),
        ("RHEUMEX", False, start, None),
        ("JOINTIVA", False, start, None),
        ("FLEXORAL", False, start, None),
        ("ARTHROLYN", False, start + timedelta(days=90), None),  # mid-timeline launch
        ("LEGACYBIO", False, start, start + timedelta(days=120)),  # switches out mid-timeline
    ]
    products = []
    presentations = []
    membership = []
    wac_rows = []
    for i, (name, is_brand, valid_from, leave_basket) in enumerate(names):
        pid = f"PRD{i+1:03d}"
        products.append(
            {
                "product_id": pid,
                "product_name": name,
                "is_brand": is_brand,
                "molecule": f"MOL_{name[:4]}",
                "therapeutic_area": "Rheumatology",
                "launch_date": valid_from.isoformat(),
            }
        )
        for strength_i, strength in enumerate(("50MG", "100MG")):
            for pack in (1, 4):
                ndc9 = f"{10000+i:05d}{strength_i+1:03d}{pack}"
                ndc11 = ndc9 + f"{pack:02d}"
                presentations.append(
                    {
                        "product_id": pid,
                        "ndc9": ndc9[:9],
                        "ndc11": ndc11[:11].ljust(11, "0")[:11],
                        "strength": strength,
                        "pack_size": pack,
                        "units_per_pack": pack,
                        "standard_units_factor": 1.0 if strength == "50MG" else 2.0,
                        "uom_default": "EA",
                    }
                )
        membership.append(
            {
                "market_id": MARKET_ID,
                "product_id": pid,
                "valid_from": valid_from.isoformat(),
                "valid_to": leave_basket.isoformat() if leave_basket else "9999-12-31",
                "is_current": leave_basket is None,
            }
        )
        if leave_basket:
            # switches into alternate basket
            membership.append(
                {
                    "market_id": "MKT_LEGACY",
                    "product_id": pid,
                    "valid_from": leave_basket.isoformat(),
                    "valid_to": "9999-12-31",
                    "is_current": True,
                }
            )
        base_wac = float(rng.uniform(800, 4000))
        for m in range(profile.n_months + 1):
            d = start + timedelta(days=30 * m)
            wac_rows.append(
                {
                    "product_id": pid,
                    "valid_from": d.isoformat(),
                    "valid_to": (d + timedelta(days=30)).isoformat(),
                    "wac": round(base_wac * (1 + 0.01 * m), 2),
                }
            )
    return ProductBundle(
        products=pd.DataFrame(products),
        presentations=pd.DataFrame(presentations),
        wac_history=pd.DataFrame(wac_rows),
        market_membership=pd.DataFrame(membership),
    )
