import sqlite3
from datetime import timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DB_PATH = "data/rates.db"

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Bangalore Daily Rates",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DATA LOADING
# ============================================================
@st.cache_data(ttl=300)
def load_gold():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT date, city,
               COALESCE(gold_22k_official, gold_22k) AS rate_22k,
               COALESCE(gold_24k_official, gold_24k) AS rate_24k,
               gold_22k AS live_22k,
               gold_24k AS live_24k,
               gold_22k_official AS official_22k,
               gold_24k_official AS official_24k,
               source
        FROM gold_rates
        ORDER BY date
    """, conn, parse_dates=["date"])
    conn.close()
    return df

@st.cache_data(ttl=300)
def load_fuel():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT date, city, petrol, diesel, source
        FROM fuel_rates
        ORDER BY date
    """, conn, parse_dates=["date"])
    conn.close()
    return df

# ============================================================
# HELPERS
# ============================================================
def delta_str(today_val, prev_val):
    if today_val is None or prev_val is None:
        return None
    diff = today_val - prev_val
    if diff == 0:
        return "No change"
    return f"{diff:+.2f} vs previous"

def latest_two(df, col):
    s = df.dropna(subset=[col]).sort_values("date")
    if len(s) >= 2:
        return s.iloc[-1][col], s.iloc[-2][col]
    elif len(s) == 1:
        return s.iloc[-1][col], None
    return None, None

# ============================================================
# LOAD DATA
# ============================================================
gold_df = load_gold()
fuel_df = load_fuel()

if gold_df.empty and fuel_df.empty:
    st.error("No data found. Run `python main.py` first to populate the database.")
    st.stop()

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("⚙️ Filters")

min_date = min(
    gold_df["date"].min() if not gold_df.empty else pd.Timestamp.today(),
    fuel_df["date"].min() if not fuel_df.empty else pd.Timestamp.today(),
).date()
max_date = max(
    gold_df["date"].max() if not gold_df.empty else pd.Timestamp.today(),
    fuel_df["date"].max() if not fuel_df.empty else pd.Timestamp.today(),
).date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(max(min_date, max_date - timedelta(days=30)), max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Data source:** BankBazaar  \n"
    f"**Last updated:** {max_date.strftime('%d %b %Y')}  \n"
    f"**Total records:** {len(gold_df) + len(fuel_df)}"
)

gold_f = gold_df[(gold_df["date"].dt.date >= start_date) &
                 (gold_df["date"].dt.date <= end_date)]
fuel_f = fuel_df[(fuel_df["date"].dt.date >= start_date) &
                 (fuel_df["date"].dt.date <= end_date)]

# ============================================================
# HEADER
# ============================================================
st.title("📊 Bangalore Daily Rates Tracker")
st.caption("Gold and fuel prices in Bangalore — live and historical trends")
st.markdown("---")

# ============================================================
# KPI CARDS
# ============================================================
st.subheader("Latest Snapshot")

col1, col2, col3, col4 = st.columns(4)

g22_today, g22_prev = latest_two(gold_df, "rate_22k")
g24_today, g24_prev = latest_two(gold_df, "rate_24k")
p_today, p_prev = latest_two(fuel_df, "petrol")
d_today, d_prev = latest_two(fuel_df, "diesel")

with col1:
    st.metric("Gold 22K (per gram)",
              f"₹{g22_today:,.0f}" if g22_today else "—",
              delta_str(g22_today, g22_prev))
with col2:
    st.metric("Gold 24K (per gram)",
              f"₹{g24_today:,.0f}" if g24_today else "—",
              delta_str(g24_today, g24_prev))
with col3:
    st.metric("Petrol (per litre)",
              f"₹{p_today:.2f}" if p_today else "—",
              delta_str(p_today, p_prev))
with col4:
    st.metric("Diesel (per litre)",
              f"₹{d_today:.2f}" if d_today else "—",
              delta_str(d_today, d_prev))

st.markdown("---")

# ============================================================
# TABS WITH CHARTS
# ============================================================
tab_gold, tab_fuel, tab_data = st.tabs(["🥇 Gold Trend", "⛽ Fuel Trend", "🗂 Raw Data"])

with tab_gold:
    if gold_f.empty:
        st.info("No gold data in this date range.")
    else:
        karat = st.radio("Karat", ["22K", "24K", "Both"], horizontal=True, index=2)
        fig = go.Figure()
        if karat in ("22K", "Both"):
            fig.add_trace(go.Scatter(
                x=gold_f["date"], y=gold_f["rate_22k"],
                mode="lines+markers", name="22K",
                line=dict(color="#D4AF37", width=2.5)))
        if karat in ("24K", "Both"):
            fig.add_trace(go.Scatter(
                x=gold_f["date"], y=gold_f["rate_24k"],
                mode="lines+markers", name="24K",
                line=dict(color="#FFD700", width=2.5)))
        fig.update_layout(
            title="Gold Rate Trend (per gram)",
            xaxis_title="Date", yaxis_title="Rate (₹)",
            hovermode="x unified", height=450, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

with tab_fuel:
    if fuel_f.empty:
        st.info("No fuel data in this date range.")
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fuel_f["date"], y=fuel_f["petrol"],
            mode="lines+markers", name="Petrol",
            line=dict(color="#E74C3C", width=2.5)))
        fig.add_trace(go.Scatter(
            x=fuel_f["date"], y=fuel_f["diesel"],
            mode="lines+markers", name="Diesel",
            line=dict(color="#3498DB", width=2.5)))
        fig.update_layout(
            title="Fuel Rate Trend (per litre)",
            xaxis_title="Date", yaxis_title="Rate (₹)",
            hovermode="x unified", height=450, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

with tab_data:
    st.markdown("#### Gold Records")
    st.dataframe(
        gold_f.assign(date=gold_f["date"].dt.strftime("%Y-%m-%d"))
              [["date", "city", "live_22k", "official_22k",
                "live_24k", "official_24k", "source"]],
        use_container_width=True, hide_index=True)
    st.download_button("Download gold CSV",
        gold_f.to_csv(index=False).encode("utf-8"),
        "gold_rates.csv", "text/csv")

    st.markdown("#### Fuel Records")
    st.dataframe(
        fuel_f.assign(date=fuel_f["date"].dt.strftime("%Y-%m-%d"))
              [["date", "city", "petrol", "diesel", "source"]],
        use_container_width=True, hide_index=True)
    st.download_button("Download fuel CSV",
        fuel_f.to_csv(index=False).encode("utf-8"),
        "fuel_rates.csv", "text/csv")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption(
    "Built By Balakrishna")
