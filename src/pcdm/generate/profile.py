"""Data profile report writer."""

from __future__ import annotations

from pathlib import Path


def write_data_profile(root: Path, scale: str, world, hcps, products, defects) -> None:
    docs = root / "docs" / "sources"
    docs.mkdir(parents=True, exist_ok=True)
    stats = world.defect_stats
    lines = [
        f"# Data Profile ({scale})",
        "",
        "Auto-generated from the synthetic generator. Synthetic ZIP space uses `9xxxx` only.",
        "",
        "## Row counts",
        f"- rx_demand rows: {len(world.rx_demand)}",
        f"- shipment lines: {len(world.shipments)}",
        f"- SP dispenses: {len(world.sp_funnel['sp_dispense'])}",
        f"- HCP entities: {len(hcps.hcps)}",
        f"- Products: {len(products.products)}",
        "",
        "## Realized defect stats",
        f"- unmatched_prescriber_rate: {stats.get('unmatched_prescriber_rate', 0):.4f}",
        f"- suppressed_cells: {stats.get('suppressed_cells', 0)}",
        f"- true_duplicates: {stats.get('true_duplicates', 0)}",
        f"- false_friends: {stats.get('false_friends', 0)}",
        "",
        "## Notes",
        "- Demand is Xponent-*style* projected retail volume (`rx_demand`), not a proprietary layout copy.",
        "- Specialty channel is under-represented in retail demand by construction.",
        "- NBRx is only available from specialty patient history.",
        "",
    ]
    (docs / "data-profile.md").write_text("\n".join(lines), encoding="utf-8")
