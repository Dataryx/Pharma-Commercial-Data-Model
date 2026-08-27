"""MDM matching: deterministic + probabilistic (lightweight Fellegi–Sunter-style)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import jellyfish
import networkx as nx
import numpy as np
import pandas as pd
import yaml


@dataclass
class MdmConfig:
    upper_threshold: float = 8.0
    lower_threshold: float = 2.0
    max_cluster_size: int = 12


def load_mdm_config(path) -> MdmConfig:
    if path and path.exists():
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return MdmConfig(
            upper_threshold=float(raw.get("upper_threshold", 8.0)),
            lower_threshold=float(raw.get("lower_threshold", 2.0)),
            max_cluster_size=int(raw.get("max_cluster_size", 12)),
        )
    return MdmConfig()


def validate_npi(npi: str | None) -> bool:
    if not npi or not str(npi).isdigit() or len(str(npi)) != 10:
        return False
    body = str(npi)
    full = "80840" + body[:9]
    total = 0
    for i, ch in enumerate(full[::-1]):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - (total % 10)) % 10) == body[9]


def jw(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    return jellyfish.jaro_winkler_similarity(str(a).upper(), str(b).upper())


def run_mdm(source_df: pd.DataFrame, cfg: MdmConfig | None = None) -> dict[str, pd.DataFrame]:
    """Return golden, xref, candidates, clusters."""
    cfg = cfg or MdmConfig()
    df = source_df.copy().reset_index(drop=True)
    df["record_uid"] = df["source_system"].astype(str) + "::" + df["source_record_id"].astype(str)

    # Deterministic edges
    edges = []  # (uid_a, uid_b, score, rule)
    for col, rule in (("npi", "DET_NPI"), ("me_number", "DET_ME"), ("dea_number", "DET_DEA")):
        valid = df[df[col].notna() & (df[col].astype(str) != "")]
        if col == "npi":
            valid = valid[valid[col].map(validate_npi)]
        for key, g in valid.groupby(col):
            uids = g["record_uid"].tolist()
            truths = g["entity_id_truth"].tolist() if "entity_id_truth" in g.columns else [None] * len(uids)
            for i in range(len(uids)):
                for j in range(i + 1, len(uids)):
                    edges.append((uids[i], uids[j], 1.0, rule))

    # Blocking + probabilistic
    df["block"] = (
        df["last_name"].fillna("").map(lambda x: jellyfish.soundex(str(x)[:20]) if str(x) else "")
        + "|"
        + df["first_name"].fillna("").astype(str).str[:1]
        + "|"
        + df["state"].fillna("")
    )
    candidates = []
    for _, g in df.groupby("block"):
        if len(g) < 2 or len(g) > 80:
            continue
        records = g.to_dict("records")
        for i in range(len(records)):
            for j in range(i + 1, len(records)):
                a, b = records[i], records[j]
                weight = _pair_weight(a, b)
                candidates.append(
                    {
                        "record_uid_a": a["record_uid"],
                        "record_uid_b": b["record_uid"],
                        "weight": weight,
                        "decision": (
                            "AUTO_MERGE"
                            if weight >= cfg.upper_threshold
                            else ("REVIEW" if weight >= cfg.lower_threshold else "NO_MATCH")
                        ),
                    }
                )
                if weight >= cfg.upper_threshold:
                    edges.append((a["record_uid"], b["record_uid"], weight, "PROB_FS"))

    G = nx.Graph()
    for uid in df["record_uid"]:
        G.add_node(uid)
    for a, b, score, rule in edges:
        # conflict guard: different valid NPIs
        ra = df.loc[df["record_uid"] == a].iloc[0]
        rb = df.loc[df["record_uid"] == b].iloc[0]
        if validate_npi(ra.get("npi")) and validate_npi(rb.get("npi")) and str(ra["npi"]) != str(rb["npi"]):
            continue
        if ra.get("me_number") and rb.get("me_number") and str(ra["me_number"]) != str(rb["me_number"]):
            if validate_npi(ra.get("npi")) and validate_npi(rb.get("npi")) and str(ra["npi"]) == str(rb["npi"]):
                pass
            elif rule.startswith("DET_NPI"):
                pass
            else:
                continue
        G.add_edge(a, b, score=score, rule=rule)

    clusters = []
    xref_rows = []
    golden_rows = []
    cluster_id = 0
    for comp in nx.connected_components(G):
        members = list(comp)
        if len(members) > cfg.max_cluster_size:
            # split to singletons pending review
            for m in members:
                cluster_id += 1
                clusters.append({"cluster_id": f"C{cluster_id:06d}", "record_uid": m, "review": True})
                xref_rows.append(_xref_row(df, m, f"H{cluster_id:06d}", 0.5, "SIZE_GUARD"))
                golden_rows.append(_survive(df, [m], f"H{cluster_id:06d}"))
            continue
        cluster_id += 1
        cid = f"C{cluster_id:06d}"
        hcp_key = f"H{cluster_id:06d}"
        for m in members:
            clusters.append({"cluster_id": cid, "record_uid": m, "review": False})
            xref_rows.append(_xref_row(df, m, hcp_key, 1.0, "CLUSTER"))
        golden_rows.append(_survive(df, members, hcp_key))

    golden = pd.DataFrame(golden_rows).drop_duplicates(subset=["hcp_key"])
    xref = pd.DataFrame(xref_rows)
    cand = pd.DataFrame(candidates)
    clus = pd.DataFrame(clusters)
    return {"golden": golden, "xref": xref, "candidates": cand, "clusters": clus}


def _pair_weight(a: dict, b: dict) -> float:
    w = 0.0
    lj = jw(a.get("last_name"), b.get("last_name"))
    if lj >= 0.90:
        w += 4.0
    elif lj >= 0.80:
        w += 1.5
    fj = jw(a.get("first_name"), b.get("first_name"))
    if fj >= 0.90:
        w += 3.0
    elif fj >= 0.80:
        w += 1.0
    if a.get("zip5") and a.get("zip5") == b.get("zip5"):
        w += 2.0
    elif a.get("zip5") and b.get("zip5") and str(a["zip5"])[:3] == str(b["zip5"])[:3]:
        w += 0.5
    if a.get("state") and a.get("state") == b.get("state"):
        w += 0.5
    if a.get("specialty_code") and a.get("specialty_code") == b.get("specialty_code"):
        w += 1.0
    if a.get("suffix") and b.get("suffix") and a["suffix"] != b["suffix"]:
        w -= 3.0
    if validate_npi(a.get("npi")) and validate_npi(b.get("npi")) and a["npi"] == b["npi"]:
        w += 10.0
    return w


def _xref_row(df, uid, hcp_key, score, rule):
    r = df.loc[df["record_uid"] == uid].iloc[0]
    return {
        "source_system": r["source_system"],
        "source_record_id": r["source_record_id"],
        "hcp_key": hcp_key,
        "match_score": score,
        "match_rule": rule,
        "entity_id_truth": r.get("entity_id_truth"),
        "is_manual_override": False,
    }


def _survive(df, members, hcp_key):
    rows = df[df["record_uid"].isin(members)]
    priority = {"hcp_master": 0, "crm": 1, "specialty": 2, "rx_demand": 3}
    rows = rows.assign(_pri=rows["source_system"].map(lambda s: priority.get(s, 9))).sort_values("_pri")

    def pick(col):
        for _, r in rows.iterrows():
            if col == "npi" and not validate_npi(r.get(col)):
                continue
            if pd.notna(r.get(col)) and str(r.get(col)) != "":
                return r.get(col), r["source_system"], r["source_record_id"]
        return None, None, None

    npi, npi_src, npi_id = pick("npi")
    first, f_src, f_id = pick("first_name")
    last, l_src, l_id = pick("last_name")
    addr, a_src, a_id = pick("address_line1")
    zip5, z_src, z_id = pick("zip5")
    # most restrictive do_not_contact
    dnc = bool(rows["do_not_contact"].fillna(False).any()) if "do_not_contact" in rows else False
    return {
        "hcp_key": hcp_key,
        "npi": npi,
        "npi_source_system": npi_src,
        "first_name": first,
        "last_name": last,
        "specialty_code": rows.iloc[0].get("specialty_code"),
        "practice_address1": addr,
        "practice_zip5": zip5,
        "practice_state": rows.iloc[0].get("state"),
        "do_not_contact": dnc,
        "sample_eligible": (not dnc),
        "is_active": bool(rows["is_active"].fillna(True).all()) if "is_active" in rows else True,
        "survivorship_rule_npi": "SOURCE_PRIORITY",
        "member_count": len(members),
    }


def evaluate_mdm(xref: pd.DataFrame, true_pairs: pd.DataFrame, false_friends: pd.DataFrame) -> dict:
    """Pairwise precision/recall vs ground-truth entity_id clustering."""
    if xref.empty or "entity_id_truth" not in xref.columns:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    # predicted pairs: same hcp_key
    pred_groups = xref.groupby("hcp_key")["entity_id_truth"].apply(lambda s: set(s.dropna())).to_dict()
    pred_pairs = set()
    for ents in pred_groups.values():
        ents = sorted(ents)
        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                pred_pairs.add(tuple(sorted((ents[i], ents[j]))))

    # true pairs from same entity appearing in multiple source rows is automatic;
    # plus explicit true_duplicate_pairs
    truth_map = xref.groupby("entity_id_truth")["hcp_key"].nunique()
    # Ground truth: records with same entity_id_truth should share hcp_key
    same_entity = xref.dropna(subset=["entity_id_truth"]).groupby("entity_id_truth")
    true_pairs_set = set()
    for eid, g in same_entity:
        # all source records of same truth entity should merge — represented as entity self
        true_pairs_set.add(eid)

    # Precision: among predicted merges of different truth ids, are they true duplicates?
    cross = [p for p in pred_pairs if p[0] != p[1]]
    td = set()
    if true_pairs is not None and len(true_pairs):
        for _, r in true_pairs.iterrows():
            td.add(tuple(sorted((r["entity_id_a"], r["entity_id_b"]))))
    tp = sum(1 for p in cross if p in td or p[0].rstrip("0123456789") == p[1].rstrip("0123456789"))
    # Simpler metric: cluster purity — each hcp_key should have 1 truth id (except true dups)
    impure = 0
    total = 0
    for hk, g in xref.dropna(subset=["entity_id_truth"]).groupby("hcp_key"):
        ids = set(g["entity_id_truth"])
        total += 1
        if len(ids) > 1:
            # allowed if all in true duplicate pairs
            ok = True
            ids_l = list(ids)
            for i in range(len(ids_l)):
                for j in range(i + 1, len(ids_l)):
                    pair = tuple(sorted((ids_l[i], ids_l[j])))
                    if pair not in td:
                        ok = False
            if not ok:
                impure += 1
    precision = 1 - (impure / max(1, total))

    # Recall: true duplicate pairs should share hcp_key
    recall_n = 0
    recall_d = 0
    if true_pairs is not None and len(true_pairs):
        key_map = xref.groupby("entity_id_truth")["hcp_key"].agg(lambda s: s.mode().iloc[0] if len(s) else None)
        for _, r in true_pairs.iterrows():
            recall_d += 1
            if key_map.get(r["entity_id_a"]) == key_map.get(r["entity_id_b"]):
                recall_n += 1
    recall = recall_n / max(1, recall_d) if recall_d else 1.0

    # False friends must NOT share key
    ff_ok = True
    if false_friends is not None and len(false_friends):
        key_map = xref.groupby("entity_id_truth")["hcp_key"].agg(lambda s: s.mode().iloc[0] if len(s) else None)
        for _, r in false_friends.iterrows():
            if key_map.get(r["entity_id_a"]) == key_map.get(r["entity_id_b"]) and key_map.get(r["entity_id_a"]) is not None:
                ff_ok = False
                precision = min(precision, 0.97)

    f1 = 2 * precision * recall / max(1e-9, (precision + recall))
    return {"precision": precision, "recall": recall, "f1": f1, "false_friends_separated": ff_ok}
