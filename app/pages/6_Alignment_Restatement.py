import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.db import connect, t  # noqa: E402

st.header("Alignment Restatement Impact")
con = connect()
st.dataframe(
    con.execute(
        f"select * from {t('gold', 'mart_alignment_restatement_impact')} order by abs(trx_delta) desc"
    ).df()
)
con.close()
