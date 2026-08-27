"""Specialty access funnel — conversion and time to therapy."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from db import connect, t  # noqa: E402

st.header("Specialty Funnel")
con = connect()
st.dataframe(con.execute(f"select * from {t('gold', 'mart_specialty_funnel')}").df(), use_container_width=True)
con.close()
