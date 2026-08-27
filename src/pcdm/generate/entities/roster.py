"""Rep roster with vacancies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from pcdm.generate.config import ScaleProfile
from pcdm.generate.entities.territory import TerritoryBundle


@dataclass
class RosterBundle:
    reps: pd.DataFrame
    assignments: pd.DataFrame


def generate_roster(rng: np.random.Generator, profile: ScaleProfile, territories: TerritoryBundle) -> RosterBundle:
    fake = Faker()
    Faker.seed(int(rng.integers(0, 1_000_000)) + 7)
    terr = territories.territories[
        (territories.territories["level"] == "TERRITORY")
        & (territories.territories["territory_id"] != "UNALIGNED")
        & (territories.territories["overlay_id"] == "PRIMARY")
    ]["territory_id"].tolist()
    start = date(2024, 1, 1)
    reps = []
    assigns = []
    for i, tid in enumerate(terr):
        rid = f"REP{i:04d}"
        vacant = rng.random() < 0.06
        if vacant:
            assigns.append(
                {
                    "rep_id": "VACANT",
                    "territory_id": tid,
                    "valid_from": start.isoformat(),
                    "valid_to": "9999-12-31",
                    "is_vacant": True,
                }
            )
            continue
        hire = start - timedelta(days=int(rng.integers(30, 800)))
        term = None
        if rng.random() < 0.08:
            term = start + timedelta(days=int(rng.integers(60, profile.n_months * 25)))
        reps.append(
            {
                "rep_id": rid,
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": f"{rid.lower()}@synthopharma.example",
                "hire_date": hire.isoformat(),
                "term_date": term.isoformat() if term else None,
            }
        )
        assigns.append(
            {
                "rep_id": rid,
                "territory_id": tid,
                "valid_from": start.isoformat(),
                "valid_to": term.isoformat() if term else "9999-12-31",
                "is_vacant": False,
            }
        )
        if term:
            assigns.append(
                {
                    "rep_id": "VACANT",
                    "territory_id": tid,
                    "valid_from": term.isoformat(),
                    "valid_to": "9999-12-31",
                    "is_vacant": True,
                }
            )
    return RosterBundle(reps=pd.DataFrame(reps), assignments=pd.DataFrame(assigns))
