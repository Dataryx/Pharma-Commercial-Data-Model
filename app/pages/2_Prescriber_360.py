import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.db import connect, t  # noqa: E402

st.header("Prescriber 360")
con = connect()
q = st.text_input("Search last name contains", "")
sql = f"select * from {t('gold', 'mart_prescriber_360')}"
if q:
    safe = q.replace("'", "")
    sql += f" where last_name ilike '%{safe}%'"
sql += " order by brand_trx desc nulls last limit 200"
st.dataframe(con.execute(sql).df())
con.close()
