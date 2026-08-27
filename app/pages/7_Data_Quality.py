import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.db import connect, t  # noqa: E402

st.header("Data Quality")
con = connect()
st.dataframe(con.execute(f"select * from {t('gold', 'mart_data_quality_summary')}").df())
st.subheader("MDM evaluation")
st.dataframe(con.execute(f"select * from {t('mdm', 'mdm_match_evaluation')}").df())
con.close()
