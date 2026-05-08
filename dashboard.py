import sqlite3
from datetime import timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np

DB_PATH = "data/rates.db"


#=======================================
# For trendlines
#=======================================
def get_trendline(dates, values, kind="Linear"):
    # Drop rows where either date or value is missing
    df = pd.DataFrame({"d": dates, "v": values}).dropna()
    if len(df) < 2:
        return None  # not enough data for a trend

    if kind == "7-day Moving Avg":
        # Build a series indexed by the original index so it aligns with the chart
        return values.rolling(window=7, min_periods=1).mean()

    # Linear regression on clean data
    x_numeric = (df["d"] - df["d"].min()).dt.days
    slope, intercept = np.polyfit(x_numeric, df["v"], 1)

    # Compute trendline for ALL original dates (including originally-NaN rows)
    full_x = (dates - df["d"].min()).dt.days
    return slope * full_x + intercept
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
def delta_info(today_val, prev_val):
    """Returns (delta_text, color) for st.metric."""
    if today_val is None or prev_val is None:
        return None, "normal"
    diff = today_val - prev_val
    if diff == 0:
        return None, "off"   # no text, no arrow when unchanged
    return f"{diff:+.2f} vs previous", "normal"
    
def latest_two(df, col):
    s = df.dropna(subset=[col]).sort_values("date")
    if len(s) >= 2:
        return s.iloc[-1][col], s.iloc[-2][col]
    elif len(s) == 1:
        return s.iloc[-1][col], None
    return None, None

def month_high_low(df, col, days=30):
    """Return (high, low, today, position_pct, n_days) over the last N days.
    position_pct = where today sits between low (0%) and high (100%).
    n_days = how many days of actual data were used."""
    if df.empty or col not in df.columns:
        return None, None, None, None, 0
    cutoff = df["date"].max() - pd.Timedelta(days=days)
    recent = df[df["date"] >= cutoff].dropna(subset=[col])
    if recent.empty:
        return None, None, None, None, 0
    high = recent[col].max()
    low = recent[col].min()
    today = recent.iloc[-1][col]
    n_days = len(recent)
    if high == low:
        pos = 50
    else:
        pos = round((today - low) / (high - low) * 100)
    return high, low, today, pos, n_days
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

g22_delta, g22_color = delta_info(g22_today, g22_prev)
g24_delta, g24_color = delta_info(g24_today, g24_prev)
p_delta,   p_color   = delta_info(p_today,   p_prev)
d_delta,   d_color   = delta_info(d_today,   d_prev)

with col1:
    st.metric("Gold 22K (per gram)",
              f"₹{g22_today:,.0f}" if g22_today else "—",
              g22_delta, delta_color=g22_color)
with col2:
    st.metric("Gold 24K (per gram)",
              f"₹{g24_today:,.0f}" if g24_today else "—",
              g24_delta, delta_color=g24_color)
with col3:
    st.metric("Petrol (per litre)",
              f"₹{p_today:.2f}" if p_today else "—",
              p_delta, delta_color=p_color)
with col4:
    st.metric("Diesel (per litre)",
              f"₹{d_today:.2f}" if d_today else "—",
              d_delta, delta_color=d_color)
m1, m2, m3, m4 = st.columns(4)

def render_range_card(col, label, df, field, fmt="{:.0f}"):
    high, low, today, pos, n_days = month_high_low(df, field)
    if high is None:
        col.info(f"No {label} data yet")
        return
    with col:
        st.markdown(f"**{label}**")
        st.caption(f"Low ₹{fmt.format(low)} · High ₹{fmt.format(high)}")
        st.progress(pos / 100)
        st.caption(f"Today sits at **{pos}%** of the {n_days}-day range")

# Figure out the longest data window we have so the heading is honest
def _data_days(df, col):
    if df.empty or col not in df.columns:
        return 0
    cutoff = df["date"].max() - pd.Timedelta(days=30)
    return len(df[(df["date"] >= cutoff)].dropna(subset=[col]))

max_days = max(
    _data_days(gold_df, "rate_22k"),
    _data_days(gold_df, "rate_24k"),
    _data_days(fuel_df, "petrol"),
    _data_days(fuel_df, "diesel"),
)

if max_days <= 1:
    heading = "Recent Snapshot"
elif max_days < 30:
    heading = f"Last {max_days} Days at a Glance"
else:
    heading = "Last 30 Days at a Glance"

st.subheader(heading)

m1, m2, m3, m4 = st.columns(4)

render_range_card(m1, "Gold 22K", gold_df, "rate_22k")
render_range_card(m2, "Gold 24K", gold_df, "rate_24k")
render_range_card(m3, "Petrol",   fuel_df, "petrol", fmt="{:.2f}")
render_range_card(m4, "Diesel",   fuel_df, "diesel", fmt="{:.2f}")

# ============================================================
# TABS WITH CHARTS
# ============================================================
tab_gold, tab_fuel, tab_data = st.tabs(["🥇 Gold Trend", "⛽ Fuel Trend", "🗂 Raw Data"])

with tab_gold:
    if gold_f.empty:
        st.info("No gold data in this date range.")
    else:
        karat = st.radio("Karat", ["22K", "24K", "Both"], horizontal=True, index=2, key="gold_karat")
        trend_type = st.radio("Trend type", ["Linear", "7-day Moving Avg"], horizontal=True, key="gold_trend")
        fig = go.Figure()

        if karat in ("22K", "Both"):
            fig.add_trace(go.Scatter(
                x=gold_f["date"], y=gold_f["rate_22k"],
                mode="lines+markers", name="22K",
                line=dict(color="#B8860B", width=2.5, shape="spline"),
                marker=dict(size=7, line=dict(color="white", width=1)),
                fill="tozeroy" if karat == "22K" else None,
                fillcolor="rgba(184, 134, 11, 0.10)",
                hovertemplate="<b>22K</b><br>%{x|%d %b %Y}<br>₹%{y:,.0f} per gram<extra></extra>"))

            trend_22k = get_trendline(gold_f["date"], gold_f["rate_22k"], trend_type)
            if trend_22k is not None:
                fig.add_trace(go.Scatter(
                    x=gold_f["date"],
                    y=trend_22k,
                    mode="lines", name=f"22K {trend_type}",
                    line=dict(color="#B8860B", width=1.5, dash="dash"),
                    opacity=0.7,
                    hovertemplate="<b>22K Trend</b><br>₹%{y:,.0f}<extra></extra>"))

        if karat in ("24K", "Both"):
            fig.add_trace(go.Scatter(
                x=gold_f["date"], y=gold_f["rate_24k"],
                mode="lines+markers", name="24K",
                line=dict(color="#D4AF37", width=2.5, shape="spline"),
                marker=dict(size=7, line=dict(color="white", width=1)),
                fill="tozeroy" if karat == "24K" else None,
                fillcolor="rgba(212, 175, 55, 0.10)",
                hovertemplate="<b>24K</b><br>%{x|%d %b %Y}<br>₹%{y:,.0f} per gram<extra></extra>"))

            trend_24k = get_trendline(gold_f["date"], gold_f["rate_24k"], trend_type)
            if trend_24k is not None:
                fig.add_trace(go.Scatter(
                    x=gold_f["date"],
                    y=trend_24k,
                    mode="lines", name=f"24K {trend_type}",
                    line=dict(color="#D4AF37", width=1.5, dash="dash"),
                    opacity=0.7,
                    hovertemplate="<b>24K Trend</b><br>₹%{y:,.0f}<extra></extra>"))

        fig.update_layout(
            title=dict(text="Gold Rate Trend (per gram)",
                       font=dict(size=18, color="#1B3024")),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="Rate (₹)", gridcolor="#E5E7EB",
                       tickformat=",.0f"),
            hovermode="x unified",
            height=480,
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(orientation="h", y=1.08, x=1, xanchor="right"))
        st.plotly_chart(fig, use_container_width=True)


with tab_fuel:
    if fuel_f.empty:
        st.info("No fuel data in this date range.")
    else:
        trend_type = st.radio("Trend type", ["Linear", "7-day Moving Avg"], horizontal=True, key="fuel_trend")
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=fuel_f["date"], y=fuel_f["petrol"],
            mode="lines+markers", name="Petrol",
            line=dict(color="#E74C3C", width=2.5, shape="spline"),
            marker=dict(size=7, line=dict(color="white", width=1)),
            hovertemplate="<b>Petrol</b><br>%{x|%d %b %Y}<br>₹%{y:.2f} per litre<extra></extra>"))

        trend_petrol = get_trendline(fuel_f["date"], fuel_f["petrol"], trend_type)
        if trend_petrol is not None:
            fig.add_trace(go.Scatter(
                x=fuel_f["date"],
                y=trend_petrol,
                mode="lines", name=f"Petrol {trend_type}",
                line=dict(color="#E74C3C", width=1.5, dash="dash"),
                opacity=0.7,
                hovertemplate="<b>Petrol Trend</b><br>₹%{y:.2f}<extra></extra>"))

        fig.add_trace(go.Scatter(
            x=fuel_f["date"], y=fuel_f["diesel"],
            mode="lines+markers", name="Diesel",
            line=dict(color="#2E7D5B", width=2.5, shape="spline"),
            marker=dict(size=7, line=dict(color="white", width=1)),
            hovertemplate="<b>Diesel</b><br>%{x|%d %b %Y}<br>₹%{y:.2f} per litre<extra></extra>"))

        trend_diesel = get_trendline(fuel_f["date"], fuel_f["diesel"], trend_type)
        if trend_diesel is not None:
            fig.add_trace(go.Scatter(
                x=fuel_f["date"],
                y=trend_diesel,
                mode="lines", name=f"Diesel {trend_type}",
                line=dict(color="#2E7D5B", width=1.5, dash="dash"),
                opacity=0.7,
                hovertemplate="<b>Diesel Trend</b><br>₹%{y:.2f}<extra></extra>"))

        fig.update_layout(
            title=dict(text="Fuel Rate Trend (per litre)",
                       font=dict(size=18, color="#1B3024")),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="Rate (₹)", gridcolor="#E5E7EB",
                       tickformat=".2f"),
            hovermode="x unified",
            height=480,
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(orientation="h", y=1.08, x=1, xanchor="right"))
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
