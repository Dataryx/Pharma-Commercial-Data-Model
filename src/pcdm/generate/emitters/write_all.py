"""Write all landing files and ground truth."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pcdm.generate.emitters.edi867 import write_edi867_files


def _mkdir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_all(
    *,
    landing: Path,
    gt: Path,
    geo,
    products,
    hcos,
    hcps,
    payers,
    territories,
    alignments,
    roster,
    world,
    defects,
    seed: int,
    scale: str,
) -> None:
    # Reference
    ref = _mkdir(landing / "reference")
    prod = products.products.merge(products.presentations, on="product_id")
    prod.to_csv(ref / "product_master.csv", index=False)
    products.wac_history.to_csv(ref / "wac_history.csv", index=False)
    products.market_membership.to_csv(ref / "market_membership.csv", index=False)
    geo.zips.to_csv(ref / "geography_zips.csv", index=False)
    world.calendar.to_csv(ref / "calendar.csv", index=False)
    xref = hcos.hcos[["hco_id", "dea_number", "hin", "hco_name", "class_of_trade", "is_340b"]].dropna(subset=["dea_number"])
    xref.to_csv(ref / "dea_hin_xref.csv", index=False)

    # HCP / HCO masters (from dirty variants + clean)
    master = hcps.source_variants[hcps.source_variants["source_system"] == "hcp_master"].copy()
    _mkdir(landing / "hcp_master")
    master.to_csv(landing / "hcp_master" / "hcp_master_20240601.csv", index=False)

    _mkdir(landing / "hco_master")
    hcos.hcos.to_csv(landing / "hco_master" / "hco_master_20240601.csv", index=False)

    _mkdir(landing / "hcp_hco_affiliation")
    hcps.affiliations.to_csv(landing / "hcp_hco_affiliation" / "affiliations_20240601.csv", index=False)

    _mkdir(landing / "plan_formulary")
    payers.formulary.to_csv(landing / "plan_formulary" / "formulary_20240601.csv", index=False)
    payers.plans.to_csv(ref / "plans.csv", index=False)
    payers.payers.to_csv(ref / "payers.csv", index=False)

    # Alignments
    _mkdir(landing / "alignment" / "zip").joinpath("alignment_zip.csv")
    alignments.zip_align.to_csv(landing / "alignment" / "zip" / "alignment_zip.csv", index=False)
    _mkdir(landing / "alignment" / "account")
    alignments.account_align.to_csv(landing / "alignment" / "account" / "alignment_account.csv", index=False)
    _mkdir(landing / "alignment" / "prescriber")
    alignments.prescriber_align.to_csv(landing / "alignment" / "prescriber" / "alignment_prescriber.csv", index=False)
    alignments.versions.to_csv(ref / "alignment_versions.csv", index=False)
    territories.territories.to_csv(ref / "territories.csv", index=False)

    _mkdir(landing / "roster")
    roster.assignments.merge(roster.reps, on="rep_id", how="left").to_csv(
        landing / "roster" / "roster_weekly.csv", index=False
    )

    _mkdir(landing / "crm_calls")
    world.crm_calls.to_csv(landing / "crm_calls" / "crm_calls.csv", index=False)
    _mkdir(landing / "crm_samples")
    world.crm_samples.to_csv(landing / "crm_samples" / "crm_samples.csv", index=False)

    _mkdir(landing / "targets_goals")
    _write_targets(landing / "targets_goals" / "targets.csv", territories, products)

    # rx_demand pipe files per period (monthly rollup for demo size budget)
    rx_dir = _mkdir(landing / "rx_demand")
    rx = world.rx_demand.copy()
    truth = rx[["prescriber_id", "entity_id_truth", "period_end_date", "product_id"]].drop_duplicates()
    truth.to_csv(gt / "rx_prescriber_truth.csv", index=False)
    pub_cols = [c for c in rx.columns if c != "entity_id_truth"]
    for (period, rest), g in rx.groupby(["period_end_date", "restatement_version"]):
        fname = f"RXD_MKT_RA_BIOLOGIC_W_{period.replace('-', '')}_v{rest}.txt"
        g[pub_cols].to_csv(rx_dir / fname, sep="|", index=False)

    # specialty
    for name, df in world.sp_funnel.items():
        d = _mkdir(landing / "specialty" / name)
        df.to_csv(d / f"{name}.csv", index=False)

    # EDI 867 raw + flat
    write_edi867_files(landing, world.shipments, defects)

    # Ground truth for MDM
    hcps.hcps.to_csv(gt / "hcp_entities.csv", index=False)
    hcps.source_variants.to_csv(gt / "hcp_source_variants.csv", index=False)
    hcps.true_duplicate_pairs.to_csv(gt / "true_duplicate_pairs.csv", index=False)
    hcps.false_friend_pairs.to_csv(gt / "false_friend_pairs.csv", index=False)
    hcos.hcos.to_csv(gt / "hco_entities.csv", index=False)
    hcos.hierarchy_events.to_csv(gt / "hco_reparent_events.csv", index=False)

    stats = {
        "scale": scale,
        "seed": seed,
        "defect_stats": world.defect_stats,
        "row_counts": {
            "rx_demand": len(world.rx_demand),
            "shipments": len(world.shipments),
            "sp_dispense": len(world.sp_funnel["sp_dispense"]),
            "hcp": len(hcps.hcps),
        },
    }
    (gt / "generation_stats.json").write_text(json.dumps(stats, indent=2, default=str), encoding="utf-8")


def _write_targets(path: Path, territories, products) -> None:
    brand = products.products.loc[products.products["is_brand"], "product_id"].iloc[0]
    terr = territories.territories[
        (territories.territories["level"] == "TERRITORY") & (territories.territories["territory_id"] != "UNALIGNED")
    ]
    rows = []
    for _, t in terr.iterrows():
        rows.append(
            {
                "territory_id": t["territory_id"],
                "product_id": brand,
                "ic_period": "2024Q2",
                "goal_trx": 100.0,
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)
