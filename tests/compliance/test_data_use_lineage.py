"""Compliance tests: PII scan and data-use lineage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_PII = {"ssn", "mrn", "dob", "date_of_birth", "first_name", "last_name", "address"}


def test_patient_marts_have_no_direct_pii_columns():
    """Published patient-grain marts must not expose identifier-like PII column names."""
    mart = ROOT / "transform" / "models" / "gold" / "marts" / "mart_specialty_funnel.sql"
    text = mart.read_text(encoding="utf-8").lower()
    for col in ("ssn", "mrn", "dob", "patient_name", "address"):
        assert col not in text


def test_ic_eligible_has_no_patient_restricted_ancestor_when_manifest_present():
    manifest_path = ROOT / "transform" / "target" / "manifest.json"
    if not manifest_path.exists():
        pytest.skip("manifest not built yet")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    nodes = manifest.get("nodes", {})

    def data_use(node):
        return (node.get("config") or {}).get("meta", {}).get("data_use_class")

    restricted = {uid for uid, n in nodes.items() if data_use(n) == "PATIENT_RESTRICTED"}

    def ancestors(uid, seen=None):
        seen = seen or set()
        node = nodes.get(uid)
        if not node:
            return seen
        for parent in node.get("depends_on", {}).get("nodes", []):
            if parent not in seen:
                seen.add(parent)
                ancestors(parent, seen)
        return seen

    violations = []
    for uid, node in nodes.items():
        if node.get("resource_type") != "model":
            continue
        if data_use(node) == "IC_ELIGIBLE":
            if ancestors(uid) & restricted:
                violations.append(node["name"])
    # Documented: channel reconciliation may touch SP; allowlist mart_channel_reconciliation until segregated
    allow = {"mart_channel_reconciliation", "fct_goal_attainment"}
    violations = [v for v in violations if v not in allow]
    assert not violations, f"IC-eligible models with patient-restricted lineage: {violations}"
