"""HCO hierarchy generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from pcdm.generate.config import ScaleProfile
from pcdm.generate.entities.geography import GeographyBundle
from pcdm.generate.utils_ids import make_dea, make_hin, make_npi


COTS = ["RETAIL_CHAIN", "INDEPENDENT", "HOSPITAL", "CLINIC", "LTC", "MAIL", "SPECIALTY", "COVERED_ENTITY_340B"]


@dataclass
class HcoBundle:
    hcos: pd.DataFrame
    hierarchy_events: pd.DataFrame


def generate_hcos(rng: np.random.Generator, profile: ScaleProfile, geo: GeographyBundle) -> HcoBundle:
    n = profile.n_hco
    zips = geo.zips["zip5"].tolist()
    # 3-level: site -> parent org -> IDN
    n_idn = max(5, n // 40)
    n_parent = max(20, n // 8)
    rows = []
    idns = [f"IDN{i:03d}" for i in range(n_idn)]
    parents = []
    for i in range(n_parent):
        parents.append({"hco_id": f"ORG{i:04d}", "parent_id": idns[i % n_idn], "level": "PARENT"})
    for i, p in enumerate(parents):
        rows.append(
            {
                "hco_id": p["hco_id"],
                "hco_name": f"Health System Parent {i}",
                "class_of_trade": "HOSPITAL",
                "parent_hco_id": p["parent_id"],
                "idn_id": p["parent_id"],
                "gpo_id": f"GPO{i % 5}",
                "is_340b": False,
                "bed_count": int(rng.integers(50, 800)),
                "address_line1": f"{100+i} MAIN ST",
                "city": "SYNTH CITY",
                "state": geo.zips.iloc[i % len(geo.zips)]["state"],
                "zip5": zips[i % len(zips)],
                "dea_number": make_dea(rng),
                "hin": make_hin(rng),
                "npi_org": make_npi(rng),
                "level": "PARENT",
            }
        )
    for i, idn in enumerate(idns):
        rows.append(
            {
                "hco_id": idn,
                "hco_name": f"IDN {i}",
                "class_of_trade": "HOSPITAL",
                "parent_hco_id": None,
                "idn_id": idn,
                "gpo_id": f"GPO{i % 5}",
                "is_340b": False,
                "bed_count": None,
                "address_line1": f"{i} IDN WAY",
                "city": "SYNTH CITY",
                "state": geo.zips.iloc[i % len(geo.zips)]["state"],
                "zip5": zips[i % len(zips)],
                "dea_number": None,
                "hin": None,
                "npi_org": make_npi(rng),
                "level": "IDN",
            }
        )
    site_start = len(rows)
    n_sites = n - len(rows)
    reparent_events = []
    for i in range(max(0, n_sites)):
        parent = parents[i % len(parents)]["hco_id"]
        cot = COTS[i % len(COTS)]
        hco_id = f"SITE{i:05d}"
        rows.append(
            {
                "hco_id": hco_id,
                "hco_name": f"{cot.replace('_',' ').title()} Site {i}",
                "class_of_trade": cot,
                "parent_hco_id": parent,
                "idn_id": next(p["parent_id"] for p in parents if p["hco_id"] == parent),
                "gpo_id": f"GPO{i % 5}",
                "is_340b": cot == "COVERED_ENTITY_340B",
                "bed_count": int(rng.integers(0, 200)) if cot == "HOSPITAL" else None,
                "address_line1": f"{200+i} PRACTICE AVE",
                "city": "SYNTH CITY",
                "state": geo.zips.iloc[i % len(geo.zips)]["state"],
                "zip5": zips[i % len(zips)],
                "dea_number": make_dea(rng),
                "hin": make_hin(rng),
                "npi_org": make_npi(rng),
                "level": "SITE",
            }
        )
    # ~5% reparent mid-timeline
    sites = [r for r in rows if r["level"] == "SITE"]
    n_reparent = max(1, int(0.05 * len(sites)))
    start = date(2024, 1, 1)
    for j in range(n_reparent):
        site = sites[int(rng.integers(0, len(sites)))]
        new_parent = parents[int(rng.integers(0, len(parents)))]["hco_id"]
        reparent_events.append(
            {
                "hco_id": site["hco_id"],
                "old_parent_hco_id": site["parent_hco_id"],
                "new_parent_hco_id": new_parent,
                "effective_date": (start + timedelta(days=int(profile.n_months * 15))).isoformat(),
            }
        )
    return HcoBundle(hcos=pd.DataFrame(rows), hierarchy_events=pd.DataFrame(reparent_events))
