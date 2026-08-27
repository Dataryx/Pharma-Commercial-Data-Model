"""Prescriber search — volumes, share, calls, alignment."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from db import connect, t  # noqa: E402

st.header("Prescriber 360")
con = connect()
q = st.text_input("Last name contains", "")
sql = f"select * from {t('gold', 'mart_prescriber_360')}"
if q:
    sql += f" where last_name ilike '%{q.replace(chr(39), '')}%'"
sql += " order by brand_trx desc nulls last limit 200"
st.dataframe(con.execute(sql).df(), use_container_width=True)
con.close()
