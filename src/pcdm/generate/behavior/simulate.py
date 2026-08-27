"""World simulation: prescribing, shipments, specialty funnel, CRM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from pcdm.generate.config import MARKET_ID, PAY_TYPES, DefectConfig, ScaleProfile
from pcdm.generate.entities.alignment import AlignmentBundle
from pcdm.generate.entities.geography import GeographyBundle
from pcdm.generate.entities.hco import HcoBundle
from pcdm.generate.entities.hcp import HcpBundle
from pcdm.generate.entities.payer import PayerBundle
from pcdm.generate.entities.product import ProductBundle
from pcdm.generate.entities.roster import RosterBundle
from pcdm.generate.entities.territory import TerritoryBundle


@dataclass
class WorldBundle:
    rx_demand: pd.DataFrame
    shipments: pd.DataFrame
    sp_funnel: dict[str, pd.DataFrame]
    crm_calls: pd.DataFrame
    crm_samples: pd.DataFrame
    defect_stats: dict
    calendar: pd.DataFrame


def _week_endings(start: date, n_months: int) -> list[date]:
    # IQVIA-style Friday week endings
    d = start
    while d.weekday() != 4:
        d += timedelta(days=1)
    end = start + timedelta(days=n_months * 30)
    weeks = []
    while d <= end:
        weeks.append(d)
        d += timedelta(days=7)
    return weeks


def simulate_world(
    *,
    rng: np.random.Generator,
    profile: ScaleProfile,
    defects: DefectConfig,
    geo: GeographyBundle,
    products: ProductBundle,
    hcos: HcoBundle,
    hcps: HcpBundle,
    payers: PayerBundle,
    territories: TerritoryBundle,
    alignments: AlignmentBundle,
    roster: RosterBundle,
) -> WorldBundle:
    start = date(2024, 1, 1)
    weeks = _week_endings(start, profile.n_months)
    cal = pd.DataFrame(
        {
            "period_end_date": weeks,
            "week_of_year": [d.isocalendar()[1] for d in weeks],
            "month": [d.month for d in weeks],
            "is_holiday_week": [d.month == 12 and d.day >= 20 or (d.month == 11 and 20 <= d.day <= 30) for d in weeks],
        }
    )

    # Prefer active non-dup entities for volume sim
    writers = hcps.hcps[~hcps.hcps["entity_id"].astype(str).str.startswith("HCPDUP")].copy()
    writers["decile"] = pd.qcut(writers["volume_latent"].rank(method="first"), 10, labels=list(range(1, 11))).astype(int)
    # top decile ~55% volume: reweight
    writers["write_weight"] = writers["volume_latent"] * writers["decile"].map(lambda d: 3.0 if d >= 9 else 1.0)

    product_ids = products.products["product_id"].tolist()
    brand = products.products.loc[products.products["is_brand"], "product_id"].iloc[0]
    # preference vectors
    prefs = rng.dirichlet(np.ones(len(product_ids)), size=len(writers))

    # CRM calls influence adoption
    call_rows = []
    sample_rows = []
    reps = roster.assignments[roster.assignments["rep_id"] != "VACANT"]
    for i, w in writers.sample(frac=0.4, random_state=int(rng.integers(0, 1e6))).iterrows():
        n_calls = int(rng.integers(1, 8))
        for c in range(n_calls):
            call_date = start + timedelta(days=int(rng.integers(0, profile.n_months * 28)))
            rep = reps.iloc[int(rng.integers(0, max(1, len(reps))))]["rep_id"] if len(reps) else "REP0000"
            call_id = f"CALL{w['entity_id']}{c}"
            call_rows.append(
                {
                    "call_id": call_id,
                    "call_date": call_date.isoformat(),
                    "rep_id": rep,
                    "account_hcp_id": w["entity_id"],
                    "product_id": brand,
                    "detail_position": 1,
                    "duration_minutes": int(rng.integers(5, 40)),
                }
            )
            if rng.random() < 0.25 and w.get("sample_eligible", True) and not w.get("do_not_contact", False):
                sample_rows.append(
                    {
                        "sample_id": f"SAMP{call_id}",
                        "call_id": call_id,
                        "hcp_id": w["entity_id"],
                        "product_id": brand,
                        "quantity": int(rng.integers(1, 4)),
                        "signature_captured": True,
                        "sample_date": call_date.isoformat(),
                    }
                )
    crm_calls = pd.DataFrame(call_rows)
    crm_samples = pd.DataFrame(sample_rows)
    called = set(crm_calls["account_hcp_id"]) if len(crm_calls) else set()

    # Demand generation — sparse for demo size budgets; denser at larger scales
    rx_rows = []
    unmatched_n = 0
    suppressed_n = 0
    total_cells = 0
    plans = payers.plans["plan_id"].tolist()
    writer_keep = 0.10 if profile.name == "demo" else (0.35 if profile.name == "small" else 0.6)
    week_stride = 2 if profile.name == "demo" else 1
    active_weeks = weeks[::week_stride]
    # Precompute membership windows
    memb_idx = {
        pid: products.market_membership[
            (products.market_membership["product_id"] == pid) & (products.market_membership["market_id"] == MARKET_ID)
        ]
        for pid in product_ids
    }
    ndc9_map = {
        pid: products.presentations[products.presentations["product_id"] == pid].iloc[0]["ndc9"] for pid in product_ids
    }

    for wi, (_, w) in enumerate(writers.iterrows()):
        if rng.random() > writer_keep and w["decile"] < 8:
            continue
        pref = prefs[wi % len(prefs)].copy()
        adopts_week = int(rng.integers(0, max(1, len(active_weeks) // 2)))
        if w["entity_id"] in called:
            adopts_week = max(0, adopts_week - 3)
        base_vol = float(w["write_weight"]) * 0.25
        null_seg = wi % 7 == 0

        for week_i, week in enumerate(active_weeks):
            season = 0.7 if week.month == 12 and week.day >= 20 or (week.month == 11 and week.day >= 20) else 1.0
            if week.month == 1:
                season *= 0.85
            if week_i > 0 and rng.random() < 0.05:
                pref = 0.9 * pref + 0.1 * rng.dirichlet(np.ones(len(product_ids)))
                pref = pref / pref.sum()
            adoption = 1 / (1 + np.exp(-(week_i - adopts_week) / 3)) if week_i >= adopts_week else 0.05
            promo = 1.15 if (w["entity_id"] in called and not null_seg) else 1.0
            week_vol = base_vol * season * promo

            for pi, pid in enumerate(product_ids):
                memb = memb_idx[pid]
                if memb.empty:
                    continue
                vf = date.fromisoformat(memb.iloc[0]["valid_from"])
                vt = (
                    date.fromisoformat(memb.iloc[0]["valid_to"])
                    if memb.iloc[0]["valid_to"] != "9999-12-31"
                    else date(9999, 12, 31)
                )
                if not (vf <= week <= vt):
                    continue
                share = float(pref[pi]) * (adoption if pid == brand else 1.0)
                trx = week_vol * share
                if trx < 0.08:
                    continue
                nrx_share = float(rng.uniform(0.25, 0.45))
                nrx = round(trx * nrx_share, 4)
                rrx = round(trx - nrx, 4)
                trx = round(nrx + rrx, 4)
                pay = PAY_TYPES[int(rng.integers(0, len(PAY_TYPES)))]
                geo_id = w["practice_zip5"]
                if defects.is_on("outside_territory") and rng.random() < defects.outside_territory_write_rate:
                    geo_id = geo.zips.iloc[int(rng.integers(0, len(geo.zips)))]["zip5"]

                prescriber_id = f"RXD{w['entity_id'][3:]}"
                if defects.is_on("unmatched_prescriber") and rng.random() < defects.unmatched_prescriber_rate:
                    prescriber_id = f"UNK{int(rng.integers(0, 1e6)):06d}"
                    unmatched_n += 1

                npi = w["npi"]
                if defects.is_on("invalid_npi") and rng.random() < defects.invalid_npi_rate:
                    from pcdm.generate.utils_ids import make_npi

                    npi = make_npi(rng, invalid=True) if rng.random() < 0.5 else ""

                suppression = "N"
                metrics = dict(
                    trx_count=round(trx, 4),
                    nrx_count=round(nrx, 4),
                    rrx_count=round(rrx, 4),
                    trx_units=round(trx * float(rng.uniform(28, 90)), 4),
                    nrx_units=round(nrx * float(rng.uniform(28, 90)), 4),
                    trx_dollars=round(trx * float(rng.uniform(200, 2000)), 2),
                )
                if (
                    defects.is_on("suppression")
                    and trx < defects.suppress_volume_lt
                    and pid != brand
                    and rng.random() < 0.5
                ):
                    suppression = "Y"
                    metrics = {k: None for k in metrics}
                    suppressed_n += 1

                total_cells += 1
                for rest_v in (1, 2):
                    m = dict(metrics)
                    if rest_v == 2 and suppression == "N" and m["trx_count"] is not None:
                        m = {
                            k: (
                                round(v * float(rng.uniform(0.97, 1.03)), 4 if k != "trx_dollars" else 2)
                                if v is not None and k != "rrx_count"
                                else None
                            )
                            for k, v in m.items()
                        }
                        if m["nrx_count"] is not None and m["trx_count"] is not None:
                            m["rrx_count"] = round(m["trx_count"] - m["nrx_count"], 4)
                            m["trx_count"] = round(m["nrx_count"] + m["rrx_count"], 4)
                    rx_rows.append(
                        {
                            "data_supplier_id": "SYNTH_XP",
                            "period_type": "W",
                            "period_end_date": week.isoformat(),
                            "restatement_version": rest_v,
                            "delivery_date": (week + timedelta(days=3)).isoformat(),
                            "prescriber_id": prescriber_id,
                            "entity_id_truth": w["entity_id"],
                            "me_number": w["me_number"],
                            "npi": npi,
                            "dea_number": w["dea_number"],
                            "product_id": pid,
                            "ndc9": ndc9_map[pid],
                            "market_id": MARKET_ID,
                            "geo_type": "ZIP5",
                            "geo_id": geo_id,
                            "pay_type": pay,
                            "plan_id": plans[int(rng.integers(0, len(plans)))] if pay != "CASH" else None,
                            **m,
                            "projection_factor": round(float(rng.uniform(1.5, 4.5)), 6),
                            "sample_flag": "Y" if rng.random() < 0.7 else "N",
                            "suppression_flag": suppression,
                        }
                    )

    rx_demand = pd.DataFrame(rx_rows)

    # Shipments 867-like flat (also emitted as EDI)
    ship_rows = []
    outlets = hcos.hcos[hcos.hcos["level"] == "SITE"].head(min(60 if profile.name == "demo" else 200, len(hcos.hcos)))
    for week_i, week in enumerate(weeks):
        if profile.name == "demo" and week_i % 2 == 1:
            continue
        # Q4 stocking bump
        stock = 1.3 if week.month >= 10 else 1.0
        lag_demand_week = weeks[max(0, week_i - 1)]
        for _, out in outlets.iterrows():
            if rng.random() < 0.4:
                continue
            pid = product_ids[int(rng.integers(0, len(product_ids)))]
            qty = float(rng.lognormal(3.0, 0.8)) * stock
            transfer = "SR"
            if defects.is_on("negative_qty") and rng.random() < defects.negative_qty_rate:
                transfer = "RE"
                qty = -abs(qty)
            if defects.is_on("chargeback_zero") and rng.random() < defects.chargeback_zero_qty_rate:
                transfer = "CB"
                qty = 0.0
            uom = "PK" if out["hco_id"].endswith("0") else "EA"  # one wholesaler-style UOM drift
            ship_rows.append(
                {
                    "interchange_control_number": f"{week.strftime('%Y%m%d')}{out['hco_id'][-4:]}",
                    "group_control_number": "1",
                    "transaction_set_control_number": "0001",
                    "report_id": f"RPT{week.strftime('%Y%m%d')}",
                    "report_date": week.isoformat(),
                    "report_purpose_code": "00",
                    "line_number": int(rng.integers(1, 9999)),
                    "transfer_type_code": transfer,
                    "ndc11": products.presentations[products.presentations["product_id"] == pid].iloc[0]["ndc11"],
                    "product_id": pid,
                    "quantity": round(qty, 4),
                    "quantity_uom": uom,
                    "unit_price_wac": float(rng.uniform(500, 3000)),
                    "ship_date": week.isoformat(),
                    "invoice_number": f"INV{int(rng.integers(1e6, 9e6))}",
                    "shipto_dea": out["dea_number"],
                    "shipto_hin": out["hin"],
                    "shipto_340b_id": f"340B{out['hco_id']}" if out["is_340b"] else None,
                    "shipto_name": out["hco_name"],
                    "shipto_address": out["address_line1"],
                    "shipto_city": out["city"],
                    "shipto_state": out["state"],
                    "shipto_zip": out["zip5"],
                    "class_of_trade": out["class_of_trade"],
                    "wholesaler_id": "WHL_A" if uom == "EA" else "WHL_B",
                    "is_return": transfer == "RE",
                    "delivery_delay_days": 5 if (defects.is_on("late_867") and rng.random() < defects.late_867_rate) else 0,
                }
            )
    shipments = pd.DataFrame(ship_rows)

    sp = _simulate_specialty(rng, profile, defects, writers, products, brand, payers, start, weeks)

    defect_stats = {
        "rx_cells": total_cells,
        "unmatched_prescriber_rate": unmatched_n / max(1, total_cells),
        "suppressed_cells": suppressed_n,
        "true_duplicates": len(hcps.true_duplicate_pairs),
        "false_friends": len(hcps.false_friend_pairs),
    }

    return WorldBundle(
        rx_demand=rx_demand,
        shipments=shipments,
        sp_funnel=sp,
        crm_calls=crm_calls,
        crm_samples=crm_samples,
        defect_stats=defect_stats,
        calendar=cal,
    )


def _simulate_specialty(rng, profile, defects, writers, products, brand, payers, start, weeks):
    """Tokenized specialty funnel + dispenses."""
    n_patients = profile.n_patients
    referrals, enrollments, bvs, pas, statuses, dispenses, copays, inventory, disc = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    stages = [
        "REFERRAL",
        "ENROLLMENT",
        "BV",
        "PA",
        "APPROVED",
        "FIRST_SHIP",
        "REFILL",
        "DISCONTINUED",
    ]
    # drop rates approx
    drop = {
        "REFERRAL": 0.05,
        "ENROLLMENT": 0.08,
        "BV": 0.12,
        "PA": 0.18,
        "APPROVED": 0.05,
        "FIRST_SHIP": 0.10,
        "REFILL": 0.15,
    }
    rheumatologists = writers[writers["specialty_code"] == "207RR0500X"]
    if rheumatologists.empty:
        rheumatologists = writers.head(100)
    ndc = products.presentations[products.presentations["product_id"] == brand].iloc[0]["ndc11"]

    for i in range(n_patients):
        token1 = f"T1_{rng.integers(0, 1e12):012x}"
        token2 = f"T2_{rng.integers(0, 1e12):012x}"
        hcp = rheumatologists.iloc[i % len(rheumatologists)]
        ref_date = start + timedelta(days=int(rng.integers(0, max(1, profile.n_months * 20))))
        referrals.append(
            {
                "referral_id": f"REF{i:06d}",
                "patient_token_1": token1,
                "patient_token_2": token2,
                "prescriber_npi": hcp["npi"],
                "prescriber_entity_id": hcp["entity_id"],
                "referral_date": ref_date.isoformat(),
                "product_id": brand,
                "sp_pharmacy_id": f"SP{i % 5:02d}",
            }
        )
        cur = ref_date
        alive = True
        last_status = None
        for stage in stages:
            if not alive:
                break
            if stage in drop and rng.random() < drop[stage]:
                statuses.append(
                    {
                        "patient_token_1": token1,
                        "status_code": "DISCONTINUED",
                        "status_date": cur.isoformat(),
                        "reason_code": f"DROP_{stage}",
                        "seq": len([s for s in statuses if s["patient_token_1"] == token1]) + 1,
                    }
                )
                disc.append(
                    {
                        "patient_token_1": token1,
                        "event_date": cur.isoformat(),
                        "reason_code": f"DROP_{stage}",
                    }
                )
                alive = False
                break
            days = int(rng.integers(1, 21))
            cur = cur + timedelta(days=days)
            # rare illegal transition injection for quarantine testing
            status_code = stage
            statuses.append(
                {
                    "patient_token_1": token1,
                    "status_code": status_code,
                    "status_date": cur.isoformat(),
                    "reason_code": None,
                    "seq": len([s for s in statuses if s["patient_token_1"] == token1]) + 1,
                }
            )
            if stage == "ENROLLMENT":
                enrollments.append(
                    {
                        "patient_token_1": token1,
                        "patient_token_2": token2,
                        "program_id": "HUB_AURORIX",
                        "enrollment_date": cur.isoformat(),
                        "consent_flag": True,
                    }
                )
            if stage == "BV":
                bvs.append(
                    {
                        "patient_token_1": token1,
                        "bv_date": cur.isoformat(),
                        "coverage_outcome": rng.choice(["COVERED", "COVERED", "DENIED"]),
                        "pa_required": bool(rng.random() < 0.4),
                        "oop_estimate": round(float(rng.uniform(0, 2500)), 2),
                    }
                )
            if stage == "PA":
                pas.append(
                    {
                        "patient_token_1": token1,
                        "pa_case_id": f"PA{i:06d}",
                        "submit_date": (cur - timedelta(days=5)).isoformat(),
                        "outcome": rng.choice(["APPROVED", "APPROVED", "DENIED"]),
                        "turnaround_days": int(rng.integers(2, 20)),
                    }
                )
            if stage in ("FIRST_SHIP", "REFILL"):
                fill_n = 1 if stage == "FIRST_SHIP" else int(rng.integers(2, 6))
                for f in range(1, fill_n + 1):
                    ship = cur + timedelta(days=30 * (f - 1))
                    if defects.is_on("timezone_shift") and rng.random() < defects.timezone_shift_rate:
                        ship = ship - timedelta(days=1)
                    is_free = rng.random() < 0.05
                    dispenses.append(
                        {
                            "sp_pharmacy_id": f"SP{i % 5:02d}",
                            "dispense_id": f"DSP{i:06d}_{f}",
                            "patient_token_1": token1,
                            "patient_token_2": token2,
                            "rx_number": f"RX{i:06d}",
                            "fill_number_reported": f if rng.random() > 0.1 else int(rng.integers(1, 9)),
                            "prescriber_npi": hcp["npi"],
                            "ndc11": ndc,
                            "product_id": brand,
                            "written_date": ref_date.isoformat(),
                            "ship_date": ship.isoformat(),
                            "dispense_date": (ship + timedelta(days=1)).isoformat(),
                            "quantity": 1.0,
                            "days_supply": 28,
                            "refills_authorized": 5,
                            "refills_remaining": max(0, 5 - f),
                            "payer_type": "FREE_GOODS" if is_free else rng.choice(["COMM", "MCARE", "MCAID", "CASH"]),
                            "plan_id": payers.plans.iloc[i % len(payers.plans)]["plan_id"],
                            "copay_amount": 0.0 if is_free else round(float(rng.uniform(0, 150)), 2),
                            "assistance_amount": round(float(rng.uniform(0, 100)), 2) if rng.random() < 0.3 else 0.0,
                            "is_free_goods": is_free,
                            "ship_to_state": hcp["practice_state"],
                        }
                    )
                    if not is_free and rng.random() < 0.3:
                        copays.append(
                            {
                                "claim_id": f"CPY{i:06d}_{f}",
                                "patient_token_1": token1,
                                "dispense_id": f"DSP{i:06d}_{f}",
                                "assistance_amount": round(float(rng.uniform(10, 200)), 2),
                                "card_type": "COPAY_CARD",
                            }
                        )
            last_status = stage

    for sp_id in range(5):
        for week in weeks[::2]:
            inventory.append(
                {
                    "sp_pharmacy_id": f"SP{sp_id:02d}",
                    "ndc11": ndc,
                    "inventory_date": week.isoformat(),
                    "on_hand_units": int(rng.integers(10, 200)),
                }
            )

    return {
        "sp_referral": pd.DataFrame(referrals),
        "sp_enrollment": pd.DataFrame(enrollments),
        "sp_benefit_verification": pd.DataFrame(bvs),
        "sp_prior_auth": pd.DataFrame(pas),
        "sp_status_history": pd.DataFrame(statuses),
        "sp_dispense": pd.DataFrame(dispenses),
        "sp_copay": pd.DataFrame(copays),
        "sp_inventory": pd.DataFrame(inventory),
        "sp_discontinuation": pd.DataFrame(disc),
    }
