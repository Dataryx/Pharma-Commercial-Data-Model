"""As-reported vs current alignment impact by territory."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from db import connect, t  # noqa: E402

st.header("Alignment Restatement Impact")
con = connect()
st.dataframe(
    con.execute(
        f"""
        select *
        from {t('gold', 'mart_alignment_restatement_impact')}
        order by abs(trx_delta) desc
        """
    ).df(),
    use_container_width=True,
)
con.close()
