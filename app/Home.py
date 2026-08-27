import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.db import connect, t  # noqa: E402

st.set_page_config(page_title="PCDM Demo", layout="wide")
st.title("Pharma Commercial Data Model — Demo")
st.markdown(
    """
This app answers the six reference questions against the DuckDB warehouse built by `pcdm all`.

Use the sidebar pages for drill-downs.
"""
)

try:
    con = connect()
except FileNotFoundError as e:
    st.error(str(e))
else:
    try:
        brand = con.execute(
            f"""
            select period_end_date, sum(brand_trx) as brand_trx, sum(market_trx) as market_trx,
                   sum(brand_trx)/nullif(sum(market_trx),0) as share
            from {t('gold', 'mart_brand_performance_weekly')}
            group by 1 order by 1
            """
        ).df()
        st.subheader("1. Brand performance (national weekly)")
        st.line_chart(brand.set_index("period_end_date")[["brand_trx", "share"]])
        st.dataframe(brand.tail(10))
    except Exception as e:
        st.warning(f"Marts not ready: {e}")
    finally:
        con.close()
