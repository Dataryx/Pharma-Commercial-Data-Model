#!/usr/bin/env python3
"""Regenerate ERD markdown from dbt manifest (CI diff gate hook)."""

from pcdm.docs_tools import generate_erd
from pathlib import Path

if __name__ == "__main__":
    generate_erd(Path(__file__).resolve().parents[1])
    print("ERD regenerated")
