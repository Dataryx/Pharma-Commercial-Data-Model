"""Commercial Insights — home overview."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from db import connect, t  # noqa: E402

st.set_page_config(page_title="PCDM Insights", layout="wide")
st.title("Commercial Insights")
st.caption("Local demo against the DuckDB warehouse built by `pcdm all`.")

try:
    con = connect()
except FileNotFoundError as e:
    st.error(str(e))
else:
    try:
        brand = con.execute(
            f"""
            select
                period_end_date,
                sum(brand_trx) as brand_trx,
                sum(market_trx) as market_trx,
                sum(brand_trx) / nullif(sum(market_trx), 0) as share
            from {t('gold', 'mart_brand_performance_weekly')}
            group by 1
            order by 1
            """
        ).df()
        st.subheader("Brand performance (national weekly)")
        st.line_chart(brand.set_index("period_end_date")[["brand_trx", "share"]])
        st.dataframe(brand.tail(10), use_container_width=True)
    except Exception as e:
        st.warning(f"Couldn't load marts yet — rebuild with `pcdm all`. ({e})")
    finally:
        con.close()
