"""HCP generation with deliberate identity defects for MDM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from pcdm.generate.config import SPECIALTIES, DefectConfig, ScaleProfile
from pcdm.generate.entities.geography import GeographyBundle
from pcdm.generate.entities.hco import HcoBundle
from pcdm.generate.utils_ids import make_dea, make_me, make_npi


@dataclass
class HcpBundle:
    hcps: pd.DataFrame  # golden / ground truth entities
    source_variants: pd.DataFrame  # dirty per-source records
    affiliations: pd.DataFrame
    true_duplicate_pairs: pd.DataFrame
    false_friend_pairs: pd.DataFrame


FIRST_VARIANTS = {"ROBERT": "ROBT", "WILLIAM": "BILL", "JAMES": "JIM", "RICHARD": "RICH", "THOMAS": "TOM"}


def generate_hcps(
    rng: np.random.Generator,
    profile: ScaleProfile,
    geo: GeographyBundle,
    hcos: HcoBundle,
    defects: DefectConfig,
) -> HcpBundle:
    fake = Faker()
    Faker.seed(int(rng.integers(0, 1_000_000)))
    n = profile.n_hcp
    sites = hcos.hcos[hcos.hcos["level"] == "SITE"].reset_index(drop=True)
    zips = geo.zips.reset_index(drop=True)

    entities = []
    affiliations = []
    start = date(2024, 1, 1)

    for i in range(n):
        spec = SPECIALTIES[i % len(SPECIALTIES)]
        zip_row = zips.iloc[i % len(zips)]
        first = fake.first_name().upper()
        last = fake.last_name().upper()
        npi = make_npi(rng, invalid=False)
        entity_id = f"HCP{i:06d}"
        volume_latent = float(rng.lognormal(mean=2.0, sigma=1.2))  # heavy-tailed
        entities.append(
            {
                "entity_id": entity_id,
                "npi": npi,
                "me_number": make_me(rng),
                "dea_number": make_dea(rng),
                "first_name": first,
                "middle_name": fake.first_name().upper()[:1],
                "last_name": last,
                "suffix": "" if rng.random() > 0.08 else rng.choice(["JR", "SR", "III"]),
                "credential": rng.choice(["MD", "DO", "NP", "PA"]),
                "specialty_code": spec[0],
                "specialty_name": spec[1],
                "state_license": f"{zip_row['state']}{rng.integers(100000, 999999)}",
                "license_state": zip_row["state"],
                "practice_zip5": zip_row["zip5"],
                "practice_address1": f"{1000+i} MEDICAL PLZ",
                "practice_city": zip_row["city"],
                "practice_state": zip_row["state"],
                "phone": f"555{rng.integers(1000000, 9999999)}",
                "is_active": True,
                "retired_date": None,
                "relocated_date": None,
                "volume_latent": volume_latent,
                "do_not_contact": bool(rng.random() < 0.02),
                "sample_eligible": True,
            }
        )
        primary_hco = sites.iloc[i % len(sites)]["hco_id"]
        affiliations.append(
            {
                "entity_id": entity_id,
                "hco_id": primary_hco,
                "is_primary": True,
                "valid_from": start.isoformat(),
                "valid_to": "9999-12-31",
            }
        )
        if rng.random() < 0.08:
            # second practice
            other = sites.iloc[int(rng.integers(0, len(sites)))]["hco_id"]
            affiliations.append(
                {
                    "entity_id": entity_id,
                    "hco_id": other,
                    "is_primary": False,
                    "valid_from": start.isoformat(),
                    "valid_to": "9999-12-31",
                }
            )

    df = pd.DataFrame(entities)

    # 1.5% retire, 3% relocate
    n_retire = max(1, int(0.015 * n))
    n_reloc = max(1, int(0.03 * n))
    retire_idx = rng.choice(n, size=n_retire, replace=False)
    for idx in retire_idx:
        df.loc[idx, "is_active"] = False
        df.loc[idx, "retired_date"] = (start + timedelta(days=int(rng.integers(30, profile.n_months * 28)))).isoformat()
    reloc_idx = rng.choice(n, size=n_reloc, replace=False)
    for idx in reloc_idx:
        new_zip = zips.iloc[int(rng.integers(0, len(zips)))]
        df.loc[idx, "relocated_date"] = (start + timedelta(days=int(rng.integers(30, profile.n_months * 28)))).isoformat()
        df.loc[idx, "practice_zip5"] = new_zip["zip5"]
        df.loc[idx, "practice_state"] = new_zip["state"]
        df.loc[idx, "practice_city"] = new_zip["city"]

    # True duplicates 0.5%
    n_dup = max(1, int(defects.true_duplicate_rate * n))
    dup_pairs = []
    dup_src_extra = []
    chosen = rng.choice(n, size=n_dup, replace=False)
    for j, idx in enumerate(chosen):
        base = df.iloc[int(idx)]
        dup_id = f"HCPDUP{j:05d}"
        dup_pairs.append({"entity_id_a": base["entity_id"], "entity_id_b": dup_id, "match_type": "TRUE_DUPLICATE"})
        # second master record same person different formatting
        row = base.to_dict()
        row["entity_id"] = dup_id
        row["first_name"] = FIRST_VARIANTS.get(base["first_name"], base["first_name"])
        row["practice_address1"] = base["practice_address1"].replace("PLZ", "PLAZA")
        # same NPI for true duplicate
        dup_src_extra.append(row)
    if dup_src_extra:
        df = pd.concat([df, pd.DataFrame(dup_src_extra)], ignore_index=True)

    # False friends 0.3% — same name, different person/city
    n_ff = max(1, int(defects.false_friend_rate * n))
    ff_pairs = []
    ff_extra = []
    chosen_ff = rng.choice(min(n, len(df)), size=n_ff, replace=False)
    for j, idx in enumerate(chosen_ff):
        base = df.iloc[int(idx)]
        ff_id = f"HCPFF{j:05d}"
        new_zip = zips.iloc[int(rng.integers(0, len(zips)))]
        ff_pairs.append({"entity_id_a": base["entity_id"], "entity_id_b": ff_id, "match_type": "FALSE_FRIEND"})
        ff_extra.append(
            {
                **{k: base[k] for k in df.columns if k not in ("entity_id", "npi", "me_number", "dea_number", "practice_zip5", "practice_city", "practice_state", "state_license")},
                "entity_id": ff_id,
                "npi": make_npi(rng),
                "me_number": make_me(rng),
                "dea_number": make_dea(rng),
                "first_name": base["first_name"],
                "last_name": base["last_name"],
                "practice_zip5": new_zip["zip5"],
                "practice_city": new_zip["city"],
                "practice_state": new_zip["state"],
                "practice_address1": f"{9000+j} OTHER ST",
                "state_license": f"{new_zip['state']}{rng.integers(100000, 999999)}",
                "license_state": new_zip["state"],
                "volume_latent": float(rng.lognormal(2.0, 1.2)),
            }
        )
    if ff_extra:
        df = pd.concat([df, pd.DataFrame(ff_extra)], ignore_index=True)

    # Build dirty source variants
    source_rows = []
    for _, e in df.iterrows():
        for source in ("hcp_master", "crm", "rx_demand", "specialty"):
            rec = _variant_record(rng, e, source, defects)
            source_rows.append(rec)

    return HcpBundle(
        hcps=df,
        source_variants=pd.DataFrame(source_rows),
        affiliations=pd.DataFrame(affiliations),
        true_duplicate_pairs=pd.DataFrame(dup_pairs),
        false_friend_pairs=pd.DataFrame(ff_pairs),
    )


def _variant_record(rng: np.random.Generator, e: pd.Series, source: str, defects: DefectConfig) -> dict:
    first, last = e["first_name"], e["last_name"]
    addr = e["practice_address1"]
    npi = e["npi"]
    if defects.is_on("name_variant") and rng.random() < defects.name_variant_rate:
        first = FIRST_VARIANTS.get(first, first)
        if e["suffix"]:
            last = f"{last} {e['suffix']}"
    if defects.is_on("address_variant") and rng.random() < defects.address_variant_rate:
        addr = addr.replace("ST", "Street").replace("PLZ", "Plaza").replace("AVE", "Avenue")
        if rng.random() < 0.3:
            addr = addr + f" STE {int(rng.integers(1, 40))}"
    if defects.is_on("invalid_npi") and rng.random() < defects.invalid_npi_rate:
        npi = make_npi(rng, invalid=True) if rng.random() < 0.5 else ""
    vendor_prefixes = {"hcp_master": "HCP", "crm": "CRM", "rx_demand": "RXD", "specialty": "SPC"}
    vendor_id = f"{vendor_prefixes.get(source, source[:3].upper())}{e['entity_id'][3:]}"
    return {
        "source_system": source,
        "source_record_id": vendor_id,
        "entity_id_truth": e["entity_id"],
        "npi": npi,
        "me_number": e["me_number"] if source in ("hcp_master", "rx_demand") else None,
        "dea_number": e["dea_number"] if source in ("hcp_master", "crm") else None,
        "first_name": first,
        "last_name": last,
        "middle_name": e["middle_name"],
        "suffix": e["suffix"],
        "credential": e["credential"],
        "specialty_code": e["specialty_code"],
        "address_line1": addr,
        "city": e["practice_city"],
        "state": e["practice_state"],
        "zip5": e["practice_zip5"],
        "phone": e["phone"] if source != "rx_demand" else None,
        "state_license": e["state_license"] if source == "hcp_master" else None,
        "license_state": e["license_state"] if source == "hcp_master" else None,
        "is_active": e["is_active"],
        "do_not_contact": e["do_not_contact"],
    }
