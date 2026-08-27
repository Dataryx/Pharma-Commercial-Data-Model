"""Synthetic geography: ZIP5 in 9xxxx space → county → state → region."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pcdm.generate.config import STATES, ScaleProfile


@dataclass
class GeographyBundle:
    zips: pd.DataFrame
    counties: pd.DataFrame


def generate_geography(rng: np.random.Generator, profile: ScaleProfile) -> GeographyBundle:
    n = profile.n_zips
    rows = []
    counties = []
    county_id = 0
    # distribute zips across states
    for i in range(n):
        state, region, division = STATES[i % len(STATES)]
        if i % 5 == 0:
            county_id += 1
            counties.append(
                {
                    "county_id": f"CTY{county_id:04d}",
                    "county_name": f"County {county_id}",
                    "state": state,
                    "region": region,
                    "division": division,
                }
            )
        zip5 = f"9{i:04d}"  # 90000-style synthetic; padded
        zip5 = f"9{str(i).zfill(4)}"[-5:]
        if not zip5.startswith("9"):
            zip5 = "9" + zip5[1:]
        # ensure 5 digits starting with 9
        zip5 = f"9{(10000 + i) % 10000:04d}"
        pop_w = float(rng.lognormal(mean=8.0, sigma=1.0))
        rows.append(
            {
                "zip5": zip5,
                "county_id": f"CTY{county_id:04d}",
                "state": state,
                "region": region,
                "division": division,
                "population_weight": pop_w,
                "city": f"SYNTH CITY {i % 50}",
            }
        )
    zips = pd.DataFrame(rows).drop_duplicates(subset=["zip5"]).reset_index(drop=True)
    # refill if collision collapsed count
    while len(zips) < n:
        i = len(zips)
        state, region, division = STATES[i % len(STATES)]
        zip5 = f"9{(20000 + i) % 10000:04d}"
        if zip5 in set(zips["zip5"]):
            zip5 = f"9{(30000 + i) % 10000:04d}"
        zips = pd.concat(
            [
                zips,
                pd.DataFrame(
                    [
                        {
                            "zip5": zip5,
                            "county_id": f"CTY{(i // 5) + 1:04d}",
                            "state": state,
                            "region": region,
                            "division": division,
                            "population_weight": float(rng.lognormal(8.0, 1.0)),
                            "city": f"SYNTH CITY {i % 50}",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    return GeographyBundle(zips=zips.head(n), counties=pd.DataFrame(counties))
