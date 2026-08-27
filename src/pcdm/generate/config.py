"""Scale profiles, seeds, and defect toggles for the synthetic generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScaleProfile:
    name: str
    n_hcp: int
    n_hco: int
    n_months: int
    n_territories: int
    n_patients: int
    n_zips: int


SCALES: dict[str, ScaleProfile] = {
    "demo": ScaleProfile("demo", n_hcp=2000, n_hco=400, n_months=3, n_territories=40, n_patients=400, n_zips=200),
    "small": ScaleProfile("small", n_hcp=25000, n_hco=4000, n_months=36, n_territories=200, n_patients=8000, n_zips=2000),
    "large": ScaleProfile(
        "large", n_hcp=250000, n_hco=40000, n_months=36, n_territories=800, n_patients=80000, n_zips=8000
    ),
}


@dataclass
class DefectConfig:
    """Toggleable injected defects (§5.4). Rates are targets; realized rates verified in pytest."""

    unmatched_prescriber_rate: float = 0.06
    invalid_npi_rate: float = 0.04
    name_variant_rate: float = 0.25
    address_variant_rate: float = 0.40
    true_duplicate_rate: float = 0.005
    false_friend_rate: float = 0.003
    restatement_weeks: int = 4
    late_867_rate: float = 0.02
    duplicate_file_rate: float = 0.01
    negative_qty_rate: float = 0.03
    chargeback_zero_qty_rate: float = 0.02
    segment_mismatch_rate: float = 0.005
    suppress_volume_lt: float = 5.0
    timezone_shift_rate: float = 0.01
    orphan_zip_rate: float = 0.01
    outside_territory_write_rate: float = 0.06
    enabled: dict[str, bool] = field(default_factory=lambda: {})

    def is_on(self, name: str) -> bool:
        return self.enabled.get(name, True)


MIN_CELL_SIZE = 5

# Brand + competitors
BRAND_NAME = "AURORIX"
MARKET_ID = "MKT_RA_BIOLOGIC"

STATES = [
    ("CA", "West", "Pacific"),
    ("OR", "West", "Pacific"),
    ("WA", "West", "Pacific"),
    ("AZ", "West", "Mountain"),
    ("CO", "West", "Mountain"),
    ("TX", "South", "West South Central"),
    ("FL", "South", "South Atlantic"),
    ("GA", "South", "South Atlantic"),
    ("NY", "Northeast", "Middle Atlantic"),
    ("NJ", "Northeast", "Middle Atlantic"),
    ("MA", "Northeast", "New England"),
    ("PA", "Northeast", "Middle Atlantic"),
    ("IL", "Midwest", "East North Central"),
    ("OH", "Midwest", "East North Central"),
    ("MI", "Midwest", "East North Central"),
    ("MN", "Midwest", "West North Central"),
]

SPECIALTIES = [
    ("207R00000X", "Internal Medicine"),
    ("207RR0500X", "Rheumatology"),
    ("207RC0000X", "Cardiovascular Disease"),
    ("208000000X", "Pediatrics"),
    ("207Q00000X", "Family Medicine"),
    ("207RX0202X", "Medical Oncology"),
]

PAY_TYPES = ["CASH", "COMM", "MCARE_D", "MCAID", "OTHER"]

NICKNAMES = {
    "ROBT": "ROBERT",
    "BILL": "WILLIAM",
    "WM": "WILLIAM",
    "JIM": "JAMES",
    "JAS": "JAMES",
    "BOB": "ROBERT",
    "RICH": "RICHARD",
    "DICK": "RICHARD",
    "TOM": "THOMAS",
    "CHUCK": "CHARLES",
    "KATHY": "KATHERINE",
    "BETH": "ELIZABETH",
    "LIZ": "ELIZABETH",
}


def default_config() -> dict[str, Any]:
    return {
        "min_cell_size": MIN_CELL_SIZE,
        "brand_name": BRAND_NAME,
        "market_id": MARKET_ID,
        "defects": DefectConfig(),
    }
