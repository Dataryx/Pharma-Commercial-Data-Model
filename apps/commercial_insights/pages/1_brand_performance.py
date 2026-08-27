"""Brand TRx / NRx / share by territory."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from db import connect, t  # noqa: E402

st.set_page_config(page_title="Brand Performance")
st.header("Brand Performance")

con = connect()
df = con.execute(
    f"""
    select *
    from {t('gold', 'mart_brand_performance_weekly')}
    order by period_end_date desc
    limit 500
    """
).df()
terr = st.selectbox("Territory", ["(all)"] + sorted(df["territory_id"].dropna().unique().tolist()))
view = df if terr == "(all)" else df[df["territory_id"] == terr]
st.dataframe(view, use_container_width=True)
st.line_chart(view.groupby("period_end_date", as_index=True)["brand_trx"].sum())
con.close()
