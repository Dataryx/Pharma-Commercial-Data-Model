#!/usr/bin/env python3
"""Refresh Mermaid ERD markdown from the latest dbt manifest."""

from pathlib import Path

from pcdm.documentation import generate_erd

if __name__ == "__main__":
    # ops/scripts -> repo root
    generate_erd(Path(__file__).resolve().parents[2])
    print("ERD regenerated")
