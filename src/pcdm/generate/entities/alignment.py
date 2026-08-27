"""ZIP / account / prescriber alignments with mid-year realignment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from pcdm.generate.config import DefectConfig, ScaleProfile
from pcdm.generate.entities.geography import GeographyBundle
from pcdm.generate.entities.hco import HcoBundle
from pcdm.generate.entities.hcp import HcpBundle
from pcdm.generate.entities.territory import TerritoryBundle


@dataclass
class AlignmentBundle:
    zip_align: pd.DataFrame
    account_align: pd.DataFrame
    prescriber_align: pd.DataFrame
    versions: pd.DataFrame


def generate_alignments(
    rng: np.random.Generator,
    profile: ScaleProfile,
    geo: GeographyBundle,
    hcps: HcpBundle,
    hcos: HcoBundle,
    territories: TerritoryBundle,
    defects: DefectConfig,
) -> AlignmentBundle:
    start = date(2024, 1, 1)
    mid = start + timedelta(days=max(60, profile.n_months * 15))
    end = date(9999, 12, 31)
    terr_ids = territories.territories[
        (territories.territories["level"] == "TERRITORY")
        & (territories.territories["overlay_id"] == "PRIMARY")
        & (territories.territories["territory_id"] != "UNALIGNED")
    ]["territory_id"].tolist()

    versions = pd.DataFrame(
        [
            {"alignment_version_id": "ALN_V1", "effective_from": start.isoformat(), "effective_to": mid.isoformat(), "change_reason": "INITIAL"},
            {"alignment_version_id": "ALN_V2", "effective_from": mid.isoformat(), "effective_to": end.isoformat(), "change_reason": "REALIGNMENT"},
        ]
    )

    zip_rows = []
    zips = geo.zips["zip5"].tolist()
    n_orphan = max(1, int(defects.orphan_zip_rate * len(zips))) if defects.is_on("orphan_zip") else 0
    orphan_set = set(rng.choice(zips, size=min(n_orphan, len(zips)), replace=False))

    for ver_i, ver in versions.iterrows():
        # shuffle territory mapping on V2
        offset = 0 if ver_i == 0 else max(1, len(terr_ids) // 7)
        for i, z in enumerate(zips):
            if z in orphan_set and ver_i == 1:
                continue  # orphan in V2
            tid = terr_ids[(i + offset) % len(terr_ids)]
            zip_rows.append(
                {
                    "alignment_version_id": ver["alignment_version_id"],
                    "overlay_id": "PRIMARY",
                    "alignment_basis": "GEOGRAPHY",
                    "basis_key": z,
                    "territory_id": tid,
                    "weight": 1.0,
                    "valid_from": ver["effective_from"],
                    "valid_to": ver["effective_to"],
                    "change_reason": ver["change_reason"],
                }
            )

    # Inject 3 overlapping alignment cases (quarantine targets)
    if len(zip_rows) >= 3:
        for k in range(3):
            base = dict(zip_rows[k])
            base["territory_id"] = terr_ids[(k + 3) % len(terr_ids)]
            base["change_reason"] = "INJECTED_OVERLAP"
            zip_rows.append(base)

    # Account alignments (~20% of sites)
    sites = hcos.hcos[hcos.hcos["level"] == "SITE"]["hco_id"].tolist()
    acct_rows = []
    for i, hco in enumerate(sites[::5]):
        for ver in versions.to_dict("records"):
            acct_rows.append(
                {
                    "alignment_version_id": ver["alignment_version_id"],
                    "overlay_id": "PRIMARY",
                    "alignment_basis": "ACCOUNT",
                    "basis_key": hco,
                    "territory_id": terr_ids[i % len(terr_ids)],
                    "weight": 1.0,
                    "valid_from": ver["effective_from"],
                    "valid_to": ver["effective_to"],
                    "change_reason": ver["change_reason"],
                }
            )

    # Prescriber explicit alignments (~10%) + some splits
    entities = hcps.hcps["entity_id"].tolist()
    presc_rows = []
    sample = entities[::10]
    for i, eid in enumerate(sample):
        for ver in versions.to_dict("records"):
            if i % 15 == 0:
                # split credit
                t1 = terr_ids[i % len(terr_ids)]
                t2 = terr_ids[(i + 1) % len(terr_ids)]
                for tid, w in ((t1, 0.6), (t2, 0.4)):
                    presc_rows.append(
                        {
                            "alignment_version_id": ver["alignment_version_id"],
                            "overlay_id": "PRIMARY",
                            "alignment_basis": "PRESCRIBER",
                            "basis_key": eid,
                            "territory_id": tid,
                            "weight": w,
                            "valid_from": ver["effective_from"],
                            "valid_to": ver["effective_to"],
                            "change_reason": "SPLIT" if ver["change_reason"] == "REALIGNMENT" else ver["change_reason"],
                        }
                    )
            else:
                presc_rows.append(
                    {
                        "alignment_version_id": ver["alignment_version_id"],
                        "overlay_id": "PRIMARY",
                        "alignment_basis": "PRESCRIBER",
                        "basis_key": eid,
                        "territory_id": terr_ids[i % len(terr_ids)],
                        "weight": 1.0,
                        "valid_from": ver["effective_from"],
                        "valid_to": ver["effective_to"],
                        "change_reason": ver["change_reason"],
                    }
                )

    return AlignmentBundle(
        zip_align=pd.DataFrame(zip_rows),
        account_align=pd.DataFrame(acct_rows),
        prescriber_align=pd.DataFrame(presc_rows),
        versions=versions,
    )
