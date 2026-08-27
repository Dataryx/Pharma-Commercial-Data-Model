"""Orchestrates entity + behavior generation and file emission."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from pcdm.generate.config import SCALES, DefectConfig
from pcdm.generate.entities.alignment import generate_alignments
from pcdm.generate.entities.geography import generate_geography
from pcdm.generate.entities.hco import generate_hcos
from pcdm.generate.entities.hcp import generate_hcps
from pcdm.generate.entities.payer import generate_payers
from pcdm.generate.entities.product import generate_products
from pcdm.generate.entities.roster import generate_roster
from pcdm.generate.entities.territory import generate_territories
from pcdm.generate.behavior.simulate import simulate_world
from pcdm.generate.emitters.write_all import write_all
from pcdm.generate.profile import write_data_profile


def run_generate(*, scale: str, seed: int, root: Path) -> Path:
    profile = SCALES[scale]
    rng = np.random.default_rng(seed)
    defects = DefectConfig()

    out = root / "datasets" / scale
    landing = out / "landing"
    gt = out / "ground_truth"
    for p in (landing, gt):
        if p.exists():
            # wipe prior generated landing for reproducibility of directory contents
            import shutil

            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)

    geo = generate_geography(rng, profile)
    products = generate_products(rng, profile)
    hcos = generate_hcos(rng, profile, geo)
    hcps = generate_hcps(rng, profile, geo, hcos, defects)
    payers = generate_payers(rng, profile, products)
    territories = generate_territories(rng, profile)
    alignments = generate_alignments(rng, profile, geo, hcps, hcos, territories, defects)
    roster = generate_roster(rng, profile, territories)

    world = simulate_world(
        rng=rng,
        profile=profile,
        defects=defects,
        geo=geo,
        products=products,
        hcos=hcos,
        hcps=hcps,
        payers=payers,
        territories=territories,
        alignments=alignments,
        roster=roster,
    )

    write_all(
        landing=landing,
        gt=gt,
        geo=geo,
        products=products,
        hcos=hcos,
        hcps=hcps,
        payers=payers,
        territories=territories,
        alignments=alignments,
        roster=roster,
        world=world,
        defects=defects,
        seed=seed,
        scale=scale,
    )

    meta = {"scale": scale, "seed": seed, "n_hcp": profile.n_hcp, "n_months": profile.n_months}
    (out / "generate_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_data_profile(root, scale, world, hcps, products, defects)
    return out
