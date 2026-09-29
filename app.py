"""
app.py
User-friendly Streamlit dashboard for the Nifty BB Consolidation-Breakout
Screener. Run with:

    streamlit run app.py
"""

import streamlit as st
import pandas as pd

from screener import run_screener
import config

st.set_page_config(page_title="Nifty BB Breakout Screener", layout="wide")

st.title("📈 Monthly Bollinger Band Consolidation-Breakout Screener")
st.caption(
    "Universe: Nifty 500 / Midcap 150 / Smallcap 250 · "
    "Bands computed on monthly candles · checked against today's live price"
)

with st.sidebar:
    st.header("Settings")
    indices = st.multiselect(
        "Universe",
        options=["NIFTY500", "MIDCAP150", "SMALLCAP250"],
        default=["NIFTY500", "MIDCAP150", "SMALLCAP250"],
    )
    bb_window = st.slider("BB window (months)", 10, 30, config.BB_WINDOW)
    bb_std = st.slider("BB std-dev multiplier", 1.0, 3.0, float(config.BB_STD), step=0.1)
    sq_pct = st.slider("Squeeze percentile (tightness)", 0.05, 0.5, config.SQUEEZE_PERCENTILE, step=0.05)
    min_sq_months = st.slider("Min consecutive squeeze months", 1, 6, config.MIN_SQUEEZE_MONTHS)
    run_clicked = st.button("🔄 Run Screener", type="primary", use_container_width=True)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_run(idx_tuple, bb_window, bb_std, sq_pct, min_sq_months):
    config.BB_WINDOW, config.BB_STD = bb_window, bb_std
    config.SQUEEZE_PERCENTILE = sq_pct
    return run_screener(list(idx_tuple), min_squeeze_months=min_sq_months)


if run_clicked or "results" not in st.session_state:
    if not indices:
        st.warning("Pick at least one index in the sidebar.")
        st.stop()
    with st.spinner("Downloading prices and computing bands for the whole universe…"):
        try:
            st.session_state["results"] = cached_run(
                tuple(indices), bb_window, bb_std, sq_pct, min_sq_months
            )
        except Exception as exc:
            st.error(f"Screener failed: {exc}")
            st.stop()

df = st.session_state.get("results", pd.DataFrame())

if not df.empty:
    as_of = df["As_Of"].iloc[0]
    st.caption(f"Bands as of month-end **{as_of}** · live price refreshed on each run")

    tab1, tab2, tab3 = st.tabs(["🚀 Breakouts", "⏳ Building Squeeze", "📋 All Stocks"])

    def _color_breakout(v):
        if v == "Bullish":
            return "color: green; font-weight: bold"
        if v == "Bearish":
            return "color: red; font-weight: bold"
        return ""

    with tab1:
        breakouts = df[df["Breakout"] != "-"]
        st.metric("Breakouts found", len(breakouts))
        st.dataframe(
            breakouts.style.applymap(_color_breakout, subset=["Breakout"]),
            use_container_width=True,
        )

    with tab2:
        building = df[(df["Breakout"] == "-") & (df["Squeeze_Months_Prior"] >= min_sq_months)]
        st.caption("Stocks currently consolidating tightly but not yet broken out — watchlist candidates.")
        st.dataframe(building, use_container_width=True)

    with tab3:
        st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download full results (CSV)", csv, "bb_screener_results.csv", "text/csv")
else:
    st.info("Set your parameters in the sidebar and click **Run Screener**.")
