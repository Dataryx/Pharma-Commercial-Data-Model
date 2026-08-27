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
    counties_map: dict[str, dict] = {}
    for i in range(n):
        state, region, division = STATES[i % len(STATES)]
        county_id = f"CTY{(i // 5) + 1:04d}"
        if county_id not in counties_map:
            counties_map[county_id] = {
                "county_id": county_id,
                "county_name": f"County {(i // 5) + 1}",
                "state": state,
                "region": region,
                "division": division,
            }
        # Synthetic ZIP space: always 9xxxx (not real USPS)
        zip5 = f"9{(i % 10000):04d}"
        # avoid collisions within generation by using wider space via county offset
        zip5 = f"9{((i * 7) % 10000):04d}"
        rows.append(
            {
                "zip5": zip5,
                "county_id": county_id,
                "state": state,
                "region": region,
                "division": division,
                "population_weight": float(rng.lognormal(mean=8.0, sigma=1.0)),
                "city": f"SYNTH CITY {i % 50}",
            }
        )
    zips = pd.DataFrame(rows)
    # dedupe zip keeping first
    zips = zips.drop_duplicates(subset=["zip5"]).reset_index(drop=True)
    # if short, add unique zips
    seen = set(zips["zip5"])
    i = 0
    while len(zips) < n:
        cand = f"9{(5000 + i) % 10000:04d}"
        i += 1
        if cand in seen:
            continue
        state, region, division = STATES[len(zips) % len(STATES)]
        county_id = f"CTY{(len(zips) // 5) + 1:04d}"
        zips = pd.concat(
            [
                zips,
                pd.DataFrame(
                    [
                        {
                            "zip5": cand,
                            "county_id": county_id,
                            "state": state,
                            "region": region,
                            "division": division,
                            "population_weight": float(rng.lognormal(8.0, 1.0)),
                            "city": f"SYNTH CITY {len(zips) % 50}",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        seen.add(cand)
        if county_id not in counties_map:
            counties_map[county_id] = {
                "county_id": county_id,
                "county_name": f"County {len(counties_map)+1}",
                "state": state,
                "region": region,
                "division": division,
            }
    return GeographyBundle(zips=zips.head(n).reset_index(drop=True), counties=pd.DataFrame(list(counties_map.values())))
