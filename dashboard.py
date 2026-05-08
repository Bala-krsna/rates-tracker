import sqlite3
from datetime import timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np

DB_PATH = "data/rates.db"

# ============================================================
# THEME / ICONS
# ============================================================
PALETTE = {
    "gold_22k": {"accent": "#EF9F27", "bg": "#FAEEDA", "dark": "#854F0B", "line": "#BA7517"},
    "gold_24k": {"accent": "#D85A30", "bg": "#FAECE7", "dark": "#993C1D", "line": "#D85A30"},
    "petrol":   {"accent": "#378ADD", "bg": "#E6F1FB", "dark": "#185FA5", "line": "#378ADD"},
    "diesel":   {"accent": "#1D9E75", "bg": "#E1F5EE", "dark": "#0F6E56", "line": "#1D9E75"},
}

ICON_22K = '<svg width="16" height="16" viewBox="0 0 20 20"><circle cx="10" cy="10" r="8.5" fill="none" stroke="currentColor" stroke-width="1.5"/><text x="10" y="13.5" text-anchor="middle" font-size="8.5" font-weight="700" fill="currentColor" font-family="system-ui, sans-serif">22K</text></svg>'
ICON_24K = '<svg width="16" height="16" viewBox="0 0 20 20"><circle cx="10" cy="10" r="8.5" fill="none" stroke="currentColor" stroke-width="1.5"/><text x="10" y="13.5" text-anchor="middle" font-size="8.5" font-weight="700" fill="currentColor" font-family="system-ui, sans-serif">24K</text></svg>'
ICON_PETROL = '<svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="8" height="14" rx="0.5"/><line x1="3" y1="9" x2="11" y2="9"/><path d="M11 7l3 2v6.5a1 1 0 0 0 2 0V8"/></svg>'
ICON_DIESEL = '<svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 6h9v8H2z"/><path d="M11 9h4l2.5 3v2H17"/><circle cx="5" cy="15" r="1.5"/><circle cx="14" cy="15" r="1.5"/></svg>'
ICON_UP = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 17 9 11 13 15 21 7"/><polyline points="14 7 21 7 21 14"/></svg>'
ICON_DOWN = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 7 9 13 13 9 21 17"/><polyline points="14 17 21 17 21 10"/></svg>'
ICON_FLAT = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>'

DASHBOARD_CSS = """
<style>
.dash-header {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 1rem; gap: 12px; flex-wrap: wrap;
}
.dash-tag {
  font-size: 11px; color: #888; margin: 0 0 4px;
  letter-spacing: 0.6px; text-transform: uppercase; font-weight: 500;
}
.dash-livedot {
  display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: #639922; margin-right: 6px; vertical-align: middle;
  animation: livepulse 2s infinite;
}
@keyframes livepulse {
  0%   { box-shadow: 0 0 0 0 rgba(99,153,34, 0.5); }
  70%  { box-shadow: 0 0 0 6px rgba(99,153,34, 0); }
  100% { box-shadow: 0 0 0 0 rgba(99,153,34, 0); }
}
.dash-title {
  margin: 0; font-size: 22px; font-weight: 600; color: #1B3024;
  letter-spacing: -0.3px;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 1.5rem;
}
.kpi-card {
  background: #ffffff;
  border: 1px solid #E8E6DE;
  border-radius: 12px;
  padding: 16px 14px 14px;
  display: flex; flex-direction: column; gap: 12px;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s ease, transform 0.2s ease;
}
.kpi-card:hover {
  border-color: #D0CDC0;
  transform: translateY(-1px);
}
.kpi-accent {
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
}
.kpi-row { display: flex; align-items: center; gap: 8px; }
.kpi-icon {
  width: 28px; height: 28px; border-radius: 8px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.kpi-titles { flex: 1; min-width: 0; }
.kpi-title { font-size: 13px; font-weight: 600; color: #1B3024; line-height: 1.2; }
.kpi-subtitle { font-size: 10px; color: #999; line-height: 1.3; margin-top: 1px; }
.kpi-status {
  font-size: 9px; padding: 3px 7px; border-radius: 999px;
  font-weight: 700; letter-spacing: 0.4px;
}
.kpi-value-block { line-height: 1; }
.kpi-value {
  font-size: 24px; font-weight: 600; color: #1B3024;
  letter-spacing: -0.5px; line-height: 1;
}
.kpi-change {
  display: inline-flex; align-items: center; gap: 4px;
  margin-top: 8px; font-size: 11px; font-weight: 500;
}
.kpi-change.up   { color: #3B6D11; }
.kpi-change.down { color: #A32D2D; }
.kpi-change.flat { color: #888; }
.kpi-change .pct { color: #999; font-weight: 400; }
.kpi-spark { width: 100%; height: 30px; display: block; }
.kpi-range-labels {
  display: flex; justify-content: space-between;
  font-size: 10px; color: #999; margin-bottom: 5px;
}
.kpi-range-bar {
  position: relative; height: 4px; background: #F0EEE8; border-radius: 999px;
}
.kpi-range-fill {
  position: absolute; left: 0; top: 0; bottom: 0; border-radius: 999px;
}
.kpi-range-marker {
  position: absolute; top: -2px; width: 8px; height: 8px; border-radius: 50%;
  border: 1.5px solid white;
  box-shadow: 0 1px 2px rgba(0,0,0,0.15);
}
.kpi-empty {
  display: flex; align-items: center; justify-content: center;
  min-height: 180px; color: #999; font-size: 13px;
}
</style>
"""


# ============================================================
# HELPERS
# ============================================================
def get_trendline(dates, values, kind="Linear"):
    df = pd.DataFrame({"d": dates, "v": values}).dropna()
    if len(df) < 2:
        return None
    if kind == "7-day Moving Avg":
        return values.rolling(window=7, min_periods=1).mean()
    x_numeric = (df["d"] - df["d"].min()).dt.days
    slope, intercept = np.polyfit(x_numeric, df["v"], 1)
    full_x = (dates - df["d"].min()).dt.days
    return slope * full_x + intercept


def latest_two(df, col):
    s = df.dropna(subset=[col]).sort_values("date")
    if len(s) >= 2:
        return s.iloc[-1][col], s.iloc[-2][col]
    elif len(s) == 1:
        return s.iloc[-1][col], None
    return None, None


def recent_history(df, col, days=30):
    """Return chronological list of values from the last `days` days."""
    if df.empty or col not in df.columns:
        return []
    cutoff = df["date"].max() - pd.Timedelta(days=days)
    s = df[df["date"] >= cutoff].dropna(subset=[col]).sort_values("date")
    return s[col].tolist()


def build_sparkline(values, color):
    """Mini SVG line. Flat dashed line for stable/single-day data."""
    if not values:
        return f'<line x1="0" y1="18" x2="140" y2="18" stroke="{color}" stroke-width="1.5" stroke-dasharray="2 2" vector-effect="non-scaling-stroke"/>'
    if len(values) == 1 or max(values) == min(values):
        return (f'<line x1="0" y1="18" x2="140" y2="18" stroke="{color}" '
                f'stroke-width="1.5" stroke-dasharray="2 2" vector-effect="non-scaling-stroke"/>'
                f'<circle cx="140" cy="18" r="2.5" fill="{color}"/>')
    vmin, vmax = min(values), max(values)
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = (i / (n - 1)) * 140
        y = 32 - ((v - vmin) / (vmax - vmin)) * 30
        pts.append(f"{x:.1f},{y:.1f}")
    last_x, last_y = pts[-1].split(",")
    return (f'<polyline points="{" ".join(pts)}" fill="none" '
            f'stroke="{color}" stroke-width="1.75" vector-effect="non-scaling-stroke" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{last_x}" cy="{last_y}" r="2.5" fill="{color}"/>')


def status_for(values):
    """Returns (label, is_special_color) for the status pill."""
    if not values:
        return "NO DATA", False
    if len(values) == 1:
        return "DAY 1", False
    high, low, today = max(values), min(values), values[-1]
    if high == low:
        return "STABLE", False
    if today >= high:
        return "PEAK", True
    if today <= low:
        return "DIP", True
    if values[-1] > values[-2]:
        return "RISING", True
    if values[-1] < values[-2]:
        return "EASING", False
    return "HOLD", False


def fmt_money(v, decimals=0):
    return f"₹{v:,.{decimals}f}"


def build_kpi_card(label, sublabel, icon, today_val, prev_val,
                   theme, history, decimals=0):
    if today_val is None:
        return f'<div class="kpi-card"><div class="kpi-empty">No {label} data yet</div></div>'

    n_days = len(history)
    value_str = fmt_money(today_val, decimals)

    # Change pill
    if prev_val is None:
        chg_html = f'<span class="kpi-change flat">{ICON_FLAT} New entry</span>'
    elif today_val == prev_val:
        chg_html = f'<span class="kpi-change flat">{ICON_FLAT} No change</span>'
    elif today_val > prev_val:
        diff = today_val - prev_val
        pct = (diff / prev_val) * 100
        chg_html = (f'<span class="kpi-change up">{ICON_UP} +{fmt_money(diff, decimals)}'
                    f'<span class="pct">· +{pct:.2f}%</span></span>')
    else:
        diff = prev_val - today_val
        pct = (diff / prev_val) * 100
        chg_html = (f'<span class="kpi-change down">{ICON_DOWN} -{fmt_money(diff, decimals)}'
                    f'<span class="pct">· -{pct:.2f}%</span></span>')

    # Status badge
    status, special = status_for(history)
    if special:
        status_style = f'background: {theme["bg"]}; color: {theme["dark"]};'
    else:
        status_style = 'background: #F2F1EC; color: #6E6D68;'

    spark = build_sparkline(history, theme["line"])

    # Range bar
    if history and len(history) >= 2 and max(history) > min(history):
        low, high = min(history), max(history)
        pos = max(0, min(100, (today_val - low) / (high - low) * 100))
        range_html = (
            f'<div class="kpi-range-labels">'
            f'<span>{fmt_money(low, decimals)}</span>'
            f'<span style="color: {theme["dark"]}; font-weight: 500;">{fmt_money(high, decimals)}</span>'
            f'</div>'
            f'<div class="kpi-range-bar">'
            f'<div class="kpi-range-fill" style="background: {theme["accent"]}; width: {pos}%;"></div>'
            f'<div class="kpi-range-marker" style="left: calc({pos}% - 4px); background: {theme["dark"]};"></div>'
            f'</div>'
        )
    else:
        range_html = (
            f'<div class="kpi-range-labels">'
            f'<span>Building history…</span>'
            f'<span style="color: {theme["dark"]}; font-weight: 500;">Day {max(n_days, 1)}</span>'
            f'</div>'
            f'<div class="kpi-range-bar">'
            f'<div class="kpi-range-marker" style="left: calc(50% - 4px); background: {theme["dark"]};"></div>'
            f'</div>'
        )

    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-accent" style="background: {theme["accent"]};"></div>'
        f'<div class="kpi-row">'
        f'<div class="kpi-icon" style="background: {theme["bg"]}; color: {theme["dark"]};">{icon}</div>'
        f'<div class="kpi-titles">'
        f'<div class="kpi-title">{label}</div>'
        f'<div class="kpi-subtitle">{sublabel}</div>'
        f'</div>'
        f'<div class="kpi-status" style="{status_style}">{status}</div>'
        f'</div>'
        f'<div class="kpi-value-block">'
        f'<div class="kpi-value">{value_str}</div>'
        f'{chg_html}'
        f'</div>'
        f'<svg class="kpi-spark" viewBox="0 0 140 36" preserveAspectRatio="none">{spark}</svg>'
        f'<div class="kpi-range">{range_html}</div>'
        f'</div>'
    )


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Bangalore Daily Rates",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)


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
st.markdown(
    f'<div class="dash-header">'
    f'<div>'
    f'<p class="dash-tag"><span class="dash-livedot"></span>Live · {max_date.strftime("%A, %d %b %Y")}</p>'
    f'<h2 class="dash-title">📊 Bangalore daily rates</h2>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True
)


# ============================================================
# KPI CARDS — replaces the old "Latest Snapshot" + "Last N Days" sections
# ============================================================
g22_today, g22_prev = latest_two(gold_df, "rate_22k")
g24_today, g24_prev = latest_two(gold_df, "rate_24k")
p_today,   p_prev   = latest_two(fuel_df, "petrol")
d_today,   d_prev   = latest_two(fuel_df, "diesel")

g22_hist = recent_history(gold_df, "rate_22k", days=30)
g24_hist = recent_history(gold_df, "rate_24k", days=30)
p_hist   = recent_history(fuel_df, "petrol",  days=30)
d_hist   = recent_history(fuel_df, "diesel",  days=30)

cards_html = (
    build_kpi_card("Gold 22K", "per gram", ICON_22K,
                   g22_today, g22_prev, PALETTE["gold_22k"], g22_hist, decimals=0) +
    build_kpi_card("Gold 24K", "per gram", ICON_24K,
                   g24_today, g24_prev, PALETTE["gold_24k"], g24_hist, decimals=0) +
    build_kpi_card("Petrol", "per litre", ICON_PETROL,
                   p_today, p_prev, PALETTE["petrol"], p_hist, decimals=2) +
    build_kpi_card("Diesel", "per litre", ICON_DIESEL,
                   d_today, d_prev, PALETTE["diesel"], d_hist, decimals=2)
)

st.markdown(f'<div class="kpi-grid">{cards_html}</div>', unsafe_allow_html=True)


# ============================================================
# TABS WITH CHARTS  (curved spline charts kept as-is)
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
                line=dict(color="#BA7517", width=2.5, shape="spline"),
                marker=dict(size=7, line=dict(color="white", width=1)),
                fill="tozeroy" if karat == "22K" else None,
                fillcolor="rgba(186, 117, 23, 0.10)",
                hovertemplate="<b>22K</b><br>%{x|%d %b %Y}<br>₹%{y:,.0f} per gram<extra></extra>"))

            trend_22k = get_trendline(gold_f["date"], gold_f["rate_22k"], trend_type)
            if trend_22k is not None:
                fig.add_trace(go.Scatter(
                    x=gold_f["date"], y=trend_22k,
                    mode="lines", name=f"22K {trend_type}",
                    line=dict(color="#BA7517", width=1.5, dash="dash"),
                    opacity=0.7,
                    hovertemplate="<b>22K Trend</b><br>₹%{y:,.0f}<extra></extra>"))

        if karat in ("24K", "Both"):
            fig.add_trace(go.Scatter(
                x=gold_f["date"], y=gold_f["rate_24k"],
                mode="lines+markers", name="24K",
                line=dict(color="#D85A30", width=2.5, shape="spline"),
                marker=dict(size=7, line=dict(color="white", width=1)),
                fill="tozeroy" if karat == "24K" else None,
                fillcolor="rgba(216, 90, 48, 0.10)",
                hovertemplate="<b>24K</b><br>%{x|%d %b %Y}<br>₹%{y:,.0f} per gram<extra></extra>"))

            trend_24k = get_trendline(gold_f["date"], gold_f["rate_24k"], trend_type)
            if trend_24k is not None:
                fig.add_trace(go.Scatter(
                    x=gold_f["date"], y=trend_24k,
                    mode="lines", name=f"24K {trend_type}",
                    line=dict(color="#D85A30", width=1.5, dash="dash"),
                    opacity=0.7,
                    hovertemplate="<b>24K Trend</b><br>₹%{y:,.0f}<extra></extra>"))

        fig.update_layout(
            title=dict(text="Gold rate trend (per gram)",
                       font=dict(size=18, color="#1B3024")),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="Rate (₹)", gridcolor="#E5E7EB", tickformat=",.0f"),
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
            line=dict(color="#378ADD", width=2.5, shape="spline"),
            marker=dict(size=7, line=dict(color="white", width=1)),
            hovertemplate="<b>Petrol</b><br>%{x|%d %b %Y}<br>₹%{y:.2f} per litre<extra></extra>"))

        trend_petrol = get_trendline(fuel_f["date"], fuel_f["petrol"], trend_type)
        if trend_petrol is not None:
            fig.add_trace(go.Scatter(
                x=fuel_f["date"], y=trend_petrol,
                mode="lines", name=f"Petrol {trend_type}",
                line=dict(color="#378ADD", width=1.5, dash="dash"),
                opacity=0.7,
                hovertemplate="<b>Petrol Trend</b><br>₹%{y:.2f}<extra></extra>"))

        fig.add_trace(go.Scatter(
            x=fuel_f["date"], y=fuel_f["diesel"],
            mode="lines+markers", name="Diesel",
            line=dict(color="#1D9E75", width=2.5, shape="spline"),
            marker=dict(size=7, line=dict(color="white", width=1)),
            hovertemplate="<b>Diesel</b><br>%{x|%d %b %Y}<br>₹%{y:.2f} per litre<extra></extra>"))

        trend_diesel = get_trendline(fuel_f["date"], fuel_f["diesel"], trend_type)
        if trend_diesel is not None:
            fig.add_trace(go.Scatter(
                x=fuel_f["date"], y=trend_diesel,
                mode="lines", name=f"Diesel {trend_type}",
                line=dict(color="#1D9E75", width=1.5, dash="dash"),
                opacity=0.7,
                hovertemplate="<b>Diesel Trend</b><br>₹%{y:.2f}<extra></extra>"))

        fig.update_layout(
            title=dict(text="Fuel rate trend (per litre)",
                       font=dict(size=18, color="#1B3024")),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="Rate (₹)", gridcolor="#E5E7EB", tickformat=".2f"),
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
st.caption("Built by Balakrishna")
