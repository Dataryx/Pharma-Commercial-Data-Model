"""Demand vs wholesaler sales-out vs specialty dispenses."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from db import connect, t  # noqa: E402

st.header("Channel Reconciliation")
con = connect()
st.dataframe(
    con.execute(
        f"""
        select *
        from {t('gold', 'mart_channel_reconciliation')}
        order by week_ending desc
        limit 300
        """
    ).df(),
    use_container_width=True,
)
con.close()
