"""Sales force hierarchy."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pcdm.generate.config import ScaleProfile


@dataclass
class TerritoryBundle:
    territories: pd.DataFrame
    hierarchy: pd.DataFrame


def generate_territories(rng: np.random.Generator, profile: ScaleProfile) -> TerritoryBundle:
    n = profile.n_territories
    n_district = max(4, n // 5)
    n_region = max(2, n_district // 3)
    rows = []
    # nation
    rows.append(
        {
            "territory_id": "NAT01",
            "territory_name": "National",
            "level": "NATION",
            "parent_territory_id": None,
            "overlay_id": "PRIMARY",
            "is_active": True,
        }
    )
    rows.append(
        {
            "territory_id": "UNALIGNED",
            "territory_name": "Unaligned",
            "level": "TERRITORY",
            "parent_territory_id": "NAT01",
            "overlay_id": "PRIMARY",
            "is_active": True,
        }
    )
    regions = []
    for i in range(n_region):
        rid = f"REG{i:02d}"
        regions.append(rid)
        rows.append(
            {
                "territory_id": rid,
                "territory_name": f"Region {i}",
                "level": "REGION",
                "parent_territory_id": "NAT01",
                "overlay_id": "PRIMARY",
                "is_active": True,
            }
        )
    districts = []
    for i in range(n_district):
        did = f"DIST{i:03d}"
        districts.append(did)
        rows.append(
            {
                "territory_id": did,
                "territory_name": f"District {i}",
                "level": "DISTRICT",
                "parent_territory_id": regions[i % len(regions)],
                "overlay_id": "PRIMARY",
                "is_active": True,
            }
        )
    for i in range(n):
        tid = f"TERR{i:04d}"
        rows.append(
            {
                "territory_id": tid,
                "territory_name": f"Territory {i}",
                "level": "TERRITORY",
                "parent_territory_id": districts[i % len(districts)],
                "overlay_id": "PRIMARY",
                "is_active": True,
            }
        )
    # specialty overlay sample
    for i in range(max(2, n // 10)):
        rows.append(
            {
                "territory_id": f"SPTERR{i:03d}",
                "territory_name": f"Specialty Territory {i}",
                "level": "TERRITORY",
                "parent_territory_id": "NAT01",
                "overlay_id": "SPECIALTY",
                "is_active": True,
            }
        )
    terr = pd.DataFrame(rows)
    hier = terr[["territory_id", "parent_territory_id", "level", "overlay_id"]].copy()
    return TerritoryBundle(territories=terr, hierarchy=hier)
