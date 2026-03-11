import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import os
import json
from datetime import datetime
import time

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ZigZag Tracker",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CONSTANTS ───────────────────────────────────────────────────────────────
DATA_FILE = "positions.csv"
COLUMNS = [
    "script", "nse_symbol", "qty", "buy_price",
    "long_sl", "short_sl",
    "short_tgt", "long_tgt", "intermediate", "final_tgt",
]

# ─── STYLE ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:       #0a0e1a;
    --surface:  #111827;
    --card:     #151d2e;
    --border:   #1e2d45;
    --accent:   #00d4ff;
    --accent2:  #00ff9d;
    --danger:   #ff4444;
    --warning:  #ffaa00;
    --text:     #e2e8f0;
    --muted:    #64748b;
    --mono:     'IBM Plex Mono', monospace;
    --sans:     'IBM Plex Sans', sans-serif;
}

html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

/* Hide default streamlit stuff */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }

/* ── HEADER ─────────────────────────────────── */
.app-header {
    display: flex; align-items: center; gap: 16px;
    padding: 18px 0 24px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.app-logo {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}
.app-title {
    font-family: var(--mono);
    font-size: 22px; font-weight: 700;
    color: var(--accent);
    letter-spacing: -0.5px;
}
.app-sub {
    font-size: 12px; color: var(--muted);
    font-family: var(--mono);
    margin-top: 2px;
}

/* ── METRIC CARDS ───────────────────────────── */
.metric-strip {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 24px;
}
.metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
}
.metric-card.blue::before  { background: var(--accent); }
.metric-card.green::before { background: var(--accent2); }
.metric-card.red::before   { background: var(--danger); }
.metric-card.orange::before{ background: var(--warning); }
.metric-card.purple::before{ background: #a78bfa; }

.metric-label { font-size: 10px; color: var(--muted); font-family: var(--mono); text-transform: uppercase; letter-spacing: 1px; }
.metric-value { font-size: 22px; font-weight: 700; font-family: var(--mono); margin-top: 4px; }
.metric-value.blue   { color: var(--accent); }
.metric-value.green  { color: var(--accent2); }
.metric-value.red    { color: var(--danger); }
.metric-value.orange { color: var(--warning); }
.metric-value.purple { color: #a78bfa; }

/* ── SIGNAL ALERTS ──────────────────────────── */
.signal-bar {
    display: flex; gap: 10px; flex-wrap: wrap;
    margin-bottom: 20px;
}
.signal-pill {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 14px; border-radius: 50px;
    font-family: var(--mono); font-size: 12px; font-weight: 600;
    border: 1px solid;
    animation: pulse 2s infinite;
}
.signal-pill.danger {
    background: rgba(255,68,68,0.12);
    border-color: var(--danger);
    color: var(--danger);
}
.signal-pill.breakout {
    background: rgba(0,255,157,0.12);
    border-color: var(--accent2);
    color: var(--accent2);
}
.signal-pill.warning {
    background: rgba(255,170,0,0.12);
    border-color: var(--warning);
    color: var(--warning);
}
@keyframes pulse {
    0%,100% { opacity:1; }
    50%      { opacity:0.7; }
}

/* ── TABLE ──────────────────────────────────── */
.tracker-table {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 24px;
}
.table-header-row {
    display: grid;
    grid-template-columns: 130px 80px 80px 85px 85px 85px 85px 85px 90px 85px 85px 85px 100px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 12px;
}
.th {
    padding: 10px 6px;
    font-family: var(--mono); font-size: 9px;
    color: var(--muted); text-transform: uppercase;
    letter-spacing: 0.8px; text-align: right;
}
.th:first-child { text-align: left; }

.table-row {
    display: grid;
    grid-template-columns: 130px 80px 80px 85px 85px 85px 85px 85px 90px 85px 85px 85px 100px;
    padding: 0 12px;
    border-bottom: 1px solid rgba(30,45,69,0.5);
    align-items: center;
    transition: background 0.15s;
}
.table-row:hover { background: rgba(0,212,255,0.04); }
.table-row:last-child { border-bottom: none; }

.td {
    padding: 11px 6px;
    font-family: var(--mono); font-size: 11px;
    text-align: right;
}
.td.name { text-align: left; font-weight: 600; color: var(--text); font-size: 12px; }
.td.price-live { font-weight: 700; color: var(--accent); }
.td.sl { color: var(--danger); }
.td.tgt { color: var(--accent2); }
.td.loss-val { color: var(--danger); }
.td.profit-val { color: var(--accent2); }
.td.exposure { color: var(--warning); font-weight: 600; }

/* Score badge */
.score-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 36px; height: 20px; border-radius: 4px;
    font-family: var(--mono); font-size: 10px; font-weight: 700;
}
.score-danger  { background: rgba(255,68,68,0.2);  color: var(--danger); border: 1px solid rgba(255,68,68,0.4); }
.score-warning { background: rgba(255,170,0,0.2);  color: var(--warning); border: 1px solid rgba(255,170,0,0.4); }
.score-ok      { background: rgba(100,116,139,0.2); color: var(--muted); border: 1px solid rgba(100,116,139,0.3); }
.score-breakout{ background: rgba(0,255,157,0.2);  color: var(--accent2); border: 1px solid rgba(0,255,157,0.4); }

/* Signal icon column */
.signal-icon { font-size: 14px; text-align: center !important; }

/* Progress bar for proximity */
.proximity-bar-wrap { width: 100%; background: rgba(30,45,69,0.8); border-radius: 3px; height: 4px; margin-top: 3px; }
.proximity-bar { height: 4px; border-radius: 3px; }

/* ── FORM ───────────────────────────────────── */
.form-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}
.form-title {
    font-family: var(--mono); font-size: 13px; font-weight: 700;
    color: var(--accent); text-transform: uppercase; letter-spacing: 1px;
    margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
}

/* Streamlit widget overrides */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] select {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
    font-family: var(--mono) !important;
    font-size: 12px !important;
}
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(0,212,255,0.15) !important;
}
div[data-testid="stSlider"] { accent-color: var(--accent) !important; }
label, .stSlider label { color: var(--muted) !important; font-size: 11px !important; font-family: var(--mono) !important; }

/* Buttons */
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, var(--accent), #0099bb) !important;
    color: #000 !important; font-weight: 700 !important;
    font-family: var(--mono) !important; font-size: 12px !important;
    border: none !important; border-radius: 7px !important;
    padding: 8px 20px !important;
    transition: opacity 0.2s !important;
}
div[data-testid="stButton"] button:hover { opacity: 0.85 !important; }
div[data-testid="stButton"] button[kind="secondary"] {
    background: var(--surface) !important;
    color: var(--muted) !important;
    border: 1px solid var(--border) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Tabs */
div[data-testid="stTabs"] button {
    font-family: var(--mono) !important;
    font-size: 11px !important;
    color: var(--muted) !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}

/* Expander */
div[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

div[data-testid="stAlert"] {
    background: rgba(0,212,255,0.08) !important;
    border: 1px solid rgba(0,212,255,0.3) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}

.stDataFrame { background: var(--card) !important; }

/* ── TOTALS ROW ─────────────────────────────── */
.totals-row {
    display: grid;
    grid-template-columns: 130px 80px 80px 85px 85px 85px 85px 85px 90px 85px 85px 85px 100px;
    padding: 10px 12px;
    background: var(--surface);
    border-top: 1px solid var(--border);
    border-radius: 0 0 12px 12px;
}
.totals-row .td {
    font-weight: 700;
    font-size: 11px;
}
.section-tag {
    display: inline-block;
    padding: 2px 8px; border-radius: 3px;
    font-size: 9px; font-family: var(--mono); font-weight: 600;
    letter-spacing: 0.5px;
}
.tag-sl   { background: rgba(255,68,68,0.15); color: var(--danger); }
.tag-tgt  { background: rgba(0,255,157,0.15); color: var(--accent2); }
.tag-live { background: rgba(0,212,255,0.15); color: var(--accent); }
</style>
""", unsafe_allow_html=True)

# ─── DATA HELPERS ────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = np.nan
        return df
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def fmt_inr(v):
    if pd.isna(v) or v == 0: return "—"
    if abs(v) >= 1e7: return f"₹{v/1e7:.2f}Cr"
    if abs(v) >= 1e5: return f"₹{v/1e5:.1f}L"
    return f"₹{v:,.0f}"

def fmt_price(v, decimals=2):
    if pd.isna(v) or v == 0: return "—"
    return f"₹{v:,.{decimals}f}"

@st.cache_data(ttl=300)
def fetch_live_prices(symbols):
    prices = {}
    if not symbols:
        return prices
    for sym in symbols:
        if not sym or pd.isna(sym):
            continue
        try:
            ticker = sym.strip().upper()
            if not ticker.endswith(".NS"):
                ticker += ".NS"
            data = yf.download(ticker, period="1d", interval="1m",
                               progress=False, auto_adjust=True)
            if data is not None and not data.empty:
                prices[sym] = float(data["Close"].iloc[-1])
        except Exception:
            pass
    return prices

def compute_signal(row, live_price, threshold_pct):
    """Returns (signal_type, signal_score, proximity_to_sl, proximity_to_st_tgt)
    signal_type: 'danger'|'breakout'|'warning'|'ok'
    signal_score: 0-100 (100 = highest urgency)
    """
    if pd.isna(live_price) or live_price == 0:
        return "ok", 0, None, None

    buy = row.get("buy_price", 0)
    short_sl = row.get("short_sl", np.nan)
    short_tgt = row.get("short_tgt", np.nan)
    long_sl = row.get("long_sl", np.nan)

    # Proximity to short-term SL (lower band)
    sl_pct = None
    if not pd.isna(short_sl) and short_sl > 0:
        sl_pct = (live_price - short_sl) / short_sl * 100  # positive = safe, small = danger

    # Proximity to short-term TGT (upper band)
    tgt_pct = None
    if not pd.isna(short_tgt) and short_tgt > 0:
        tgt_pct = (short_tgt - live_price) / live_price * 100  # positive = not there yet

    # Signal logic
    if sl_pct is not None and sl_pct <= threshold_pct:
        if sl_pct <= 0:
            score = 100  # Breached SL
        else:
            score = int(100 - (sl_pct / threshold_pct) * 50)
        return "danger", score, sl_pct, tgt_pct

    if tgt_pct is not None and tgt_pct <= threshold_pct:
        if tgt_pct <= 0:
            score = 100  # Breached target
        else:
            score = int(100 - (tgt_pct / threshold_pct) * 50)
        return "breakout", score, sl_pct, tgt_pct

    # Mild warning: within 2x threshold of SL
    if sl_pct is not None and sl_pct <= threshold_pct * 2:
        score = int(30 - (sl_pct / (threshold_pct * 2)) * 20)
        return "warning", score, sl_pct, tgt_pct

    return "ok", 0, sl_pct, tgt_pct

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    threshold_pct = st.slider(
        "Alert Threshold (%)",
        min_value=1.0, max_value=10.0, value=3.0, step=0.5,
        help="Signal fires when price is within this % of SL or Target"
    )
    st.markdown("---")
    if st.button("🔄 Refresh Prices", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("<span style='font-size:10px;color:#64748b;font-family:monospace'>ZigZag Rotation Tracker<br>NSE Live • yfinance feed</span>", unsafe_allow_html=True)

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div class="app-logo">📡</div>
  <div>
    <div class="app-title">ZIGZAG ROTATION TRACKER</div>
    <div class="app-sub">NSE Live Feed · Signal Intelligence · Multi-Target Framework</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
df = load_data()

# ─── TABS ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Live Tracker", "➕ Add / Edit Positions", "📥 Bulk Upload"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: LIVE TRACKER
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    if df.empty:
        st.info("No positions yet. Go to **Add / Edit Positions** to add your first trade.")
    else:
        # Fetch live prices
        symbols = df["nse_symbol"].dropna().tolist()
        with st.spinner("Fetching live NSE prices..."):
            live_prices = fetch_live_prices(symbols)

        # Compute enriched data
        rows_enriched = []
        for _, row in df.iterrows():
            sym = row.get("nse_symbol", "")
            live = live_prices.get(sym, np.nan)
            signal, score, sl_pct, tgt_pct = compute_signal(row.to_dict(), live, threshold_pct)

            qty = row.get("qty", 0)
            buy = row.get("buy_price", 0)
            exposure = qty * buy if not pd.isna(qty) and not pd.isna(buy) else np.nan
            long_loss = qty * (row.get("long_sl", 0) - buy) if not pd.isna(row.get("long_sl")) else np.nan
            short_loss = qty * (row.get("short_sl", 0) - buy) if not pd.isna(row.get("short_sl")) else np.nan
            short_profit = qty * (row.get("short_tgt", 0) - buy) if not pd.isna(row.get("short_tgt")) else np.nan
            long_profit = qty * (row.get("long_tgt", 0) - buy) if not pd.isna(row.get("long_tgt")) else np.nan
            live_pnl = qty * (live - buy) if not pd.isna(live) else np.nan

            rows_enriched.append({
                **row.to_dict(),
                "live": live,
                "signal": signal,
                "score": score,
                "sl_pct": sl_pct,
                "tgt_pct": tgt_pct,
                "exposure": exposure,
                "long_loss": long_loss,
                "short_loss": short_loss,
                "short_profit": short_profit,
                "long_profit": long_profit,
                "live_pnl": live_pnl,
            })

        edf = pd.DataFrame(rows_enriched)

        # ── SIGNAL ALERTS BAR ─────────────────────────────────────────────
        danger_list   = edf[edf["signal"] == "danger"]["script"].tolist()
        breakout_list = edf[edf["signal"] == "breakout"]["script"].tolist()
        warning_list  = edf[edf["signal"] == "warning"]["script"].tolist()

        if danger_list or breakout_list or warning_list:
            pills_html = '<div class="signal-bar">'
            for s in danger_list:
                pills_html += f'<div class="signal-pill danger">🔴 {s} — NEAR SL ZONE</div>'
            for s in breakout_list:
                pills_html += f'<div class="signal-pill breakout">🟢 {s} — BREAKOUT WATCH</div>'
            for s in warning_list:
                pills_html += f'<div class="signal-pill warning">🟡 {s} — APPROACHING SL</div>'
            pills_html += "</div>"
            st.markdown(pills_html, unsafe_allow_html=True)

        # ── SUMMARY METRICS ───────────────────────────────────────────────
        total_exposure = edf["exposure"].sum()
        total_live_pnl = edf["live_pnl"].sum()
        total_short_loss = edf["short_loss"].sum()
        total_short_profit = edf["short_profit"].sum()
        total_long_profit = edf["long_profit"].sum()
        active_signals = len(danger_list) + len(breakout_list)

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f"""<div class="metric-card blue">
                <div class="metric-label">Total Exposure</div>
                <div class="metric-value blue">{fmt_inr(total_exposure)}</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            pnl_color = "green" if total_live_pnl >= 0 else "red"
            pnl_sign = "+" if total_live_pnl >= 0 else ""
            st.markdown(f"""<div class="metric-card {pnl_color}">
                <div class="metric-label">Live P&L</div>
                <div class="metric-value {pnl_color}">{pnl_sign}{fmt_inr(total_live_pnl)}</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card red">
                <div class="metric-label">Short Term Risk</div>
                <div class="metric-value red">{fmt_inr(total_short_loss)}</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="metric-card green">
                <div class="metric-label">Short TGT Profit</div>
                <div class="metric-value green">{fmt_inr(total_short_profit)}</div>
            </div>""", unsafe_allow_html=True)
        with m5:
            sig_color = "orange" if active_signals > 0 else "purple"
            st.markdown(f"""<div class="metric-card {sig_color}">
                <div class="metric-label">Active Signals</div>
                <div class="metric-value {sig_color}">{active_signals}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── POSITION TABLE ────────────────────────────────────────────────
        # Sort: danger first, then breakout, then warning, then ok; within each by score desc
        signal_order = {"danger": 0, "breakout": 1, "warning": 2, "ok": 3}
        edf["_sig_order"] = edf["signal"].map(signal_order)
        edf = edf.sort_values(["_sig_order", "score"], ascending=[True, False]).reset_index(drop=True)

        # Header
        table_html = '<div class="tracker-table">'
        table_html += '''<div class="table-header-row">
            <div class="th">Script</div>
            <div class="th">Signal</div>
            <div class="th">Live ₹</div>
            <div class="th">Buy ₹</div>
            <div class="th">Short SL</div>
            <div class="th">Long SL</div>
            <div class="th">ST TGT</div>
            <div class="th">LT TGT</div>
            <div class="th">Score</div>
            <div class="th">ST Loss</div>
            <div class="th">ST Profit</div>
            <div class="th">Live P&L</div>
            <div class="th">Exposure</div>
        </div>'''

        for _, r in edf.iterrows():
            sig = r["signal"]
            score = r["score"]
            live = r["live"]

            # Signal icon
            if sig == "danger":
                sig_icon = "🔴"
                score_cls = "score-danger"
            elif sig == "breakout":
                sig_icon = "🟢"
                score_cls = "score-breakout"
            elif sig == "warning":
                sig_icon = "🟡"
                score_cls = "score-warning"
            else:
                sig_icon = "⚪"
                score_cls = "score-ok"

            live_pnl_v = r.get("live_pnl", np.nan)
            pnl_cls = "profit-val" if (not pd.isna(live_pnl_v) and live_pnl_v >= 0) else "loss-val"
            pnl_sign = "+" if (not pd.isna(live_pnl_v) and live_pnl_v >= 0) else ""

            table_html += f'''<div class="table-row">
                <div class="td name">{r["script"]}</div>
                <div class="td signal-icon">{sig_icon}</div>
                <div class="td price-live">{fmt_price(live)}</div>
                <div class="td">{fmt_price(r.get("buy_price"))}</div>
                <div class="td sl">{fmt_price(r.get("short_sl"))}</div>
                <div class="td sl">{fmt_price(r.get("long_sl"))}</div>
                <div class="td tgt">{fmt_price(r.get("short_tgt"))}</div>
                <div class="td tgt">{fmt_price(r.get("long_tgt"))}</div>
                <div class="td"><span class="score-badge {score_cls}">{score}</span></div>
                <div class="td loss-val">{fmt_inr(r.get("short_loss"))}</div>
                <div class="td profit-val">{fmt_inr(r.get("short_profit"))}</div>
                <div class="td {pnl_cls}">{pnl_sign}{fmt_inr(live_pnl_v)}</div>
                <div class="td exposure">{fmt_inr(r.get("exposure"))}</div>
            </div>'''

        # Totals
        table_html += f'''<div class="totals-row">
            <div class="td" style="color:#64748b;font-size:10px;">TOTAL ({len(edf)})</div>
            <div class="td"></div><div class="td"></div><div class="td"></div>
            <div class="td"></div><div class="td"></div><div class="td"></div><div class="td"></div><div class="td"></div>
            <div class="td loss-val">{fmt_inr(total_short_loss)}</div>
            <div class="td profit-val">{fmt_inr(total_short_profit)}</div>
            <div class="td {'profit-val' if total_live_pnl>=0 else 'loss-val'}">{'+' if total_live_pnl>=0 else ''}{fmt_inr(total_live_pnl)}</div>
            <div class="td exposure">{fmt_inr(total_exposure)}</div>
        </div>'''

        table_html += "</div>"
        st.markdown(table_html, unsafe_allow_html=True)

        # ── SIGNAL DETAIL EXPANDER ────────────────────────────────────────
        with st.expander("📐 Signal Score Breakdown", expanded=False):
            st.markdown(f"""
            **How signals are computed** (threshold = `{threshold_pct}%`):

            | Score | Meaning |
            |-------|---------|
            | 🔴 80–100 | Price within threshold of Short SL or has breached it |
            | 🟢 50–100 | Price within threshold of Short TGT — breakout imminent |
            | 🟡 20–49  | Price within 2× threshold of SL — approaching danger zone |
            | ⚪ 0      | Position safe — no action needed |

            Score = `100 - (distance_from_trigger / threshold) × 50`
            """)

        # ── DELETE POSITIONS ──────────────────────────────────────────────
        with st.expander("🗑️ Remove a Position", expanded=False):
            if not df.empty:
                to_delete = st.selectbox("Select script to remove", df["script"].tolist())
                if st.button("Remove Position", type="primary"):
                    df = df[df["script"] != to_delete].reset_index(drop=True)
                    save_data(df)
                    st.success(f"Removed {to_delete}")
                    st.cache_data.clear()
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: ADD / EDIT
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="form-card"><div class="form-title">➕ Add New Position</div>', unsafe_allow_html=True)

    with st.form("add_position_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            script = st.text_input("Script Name", placeholder="e.g. Chambal Fert")
            nse_symbol = st.text_input("NSE Symbol", placeholder="e.g. CHAMBLFERT (no .NS needed)")
            qty = st.number_input("Quantity", min_value=1, value=100, step=1)
        with c2:
            buy_price = st.number_input("Buy Price ₹", min_value=0.01, value=100.0, step=0.05)
            long_sl = st.number_input("Long Term SL ₹", min_value=0.01, value=90.0, step=0.05)
            short_sl = st.number_input("Short Term SL ₹", min_value=0.01, value=95.0, step=0.05)
        with c3:
            short_tgt = st.number_input("Short Term TGT ₹", min_value=0.01, value=115.0, step=0.05)
            long_tgt = st.number_input("Long Term TGT ₹", min_value=0.01, value=140.0, step=0.05)
            intermediate = st.number_input("Intermediate TGT ₹ (optional)", min_value=0.0, value=0.0, step=0.05)
            final_tgt = st.number_input("Final TGT ₹ (optional)", min_value=0.0, value=0.0, step=0.05)

        submitted = st.form_submit_button("Add Position", use_container_width=True)

        if submitted:
            if not script or not nse_symbol:
                st.error("Script name and NSE symbol are required.")
            else:
                # Check duplicate
                if script in df["script"].values:
                    st.warning(f"'{script}' already exists. Edit below or remove it first.")
                else:
                    new_row = {
                        "script": script.strip(),
                        "nse_symbol": nse_symbol.strip().upper(),
                        "qty": qty,
                        "buy_price": buy_price,
                        "long_sl": long_sl,
                        "short_sl": short_sl,
                        "short_tgt": short_tgt,
                        "long_tgt": long_tgt,
                        "intermediate": intermediate if intermediate > 0 else np.nan,
                        "final_tgt": final_tgt if final_tgt > 0 else np.nan,
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df)
                    st.success(f"✅ {script} added successfully!")
                    st.cache_data.clear()
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Edit existing
    if not df.empty:
        st.markdown('<div class="form-card"><div class="form-title">✏️ Edit Existing Position</div>', unsafe_allow_html=True)
        edit_script = st.selectbox("Select position to edit", df["script"].tolist())
        edit_row = df[df["script"] == edit_script].iloc[0]

        with st.form("edit_form"):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                e_nse = st.text_input("NSE Symbol", value=str(edit_row.get("nse_symbol", "")))
                e_qty = st.number_input("Quantity", value=int(edit_row.get("qty", 100)), step=1)
                e_buy = st.number_input("Buy Price ₹", value=float(edit_row.get("buy_price", 0)), step=0.05)
            with ec2:
                e_lsl = st.number_input("Long SL ₹", value=float(edit_row.get("long_sl", 0)), step=0.05)
                e_ssl = st.number_input("Short SL ₹", value=float(edit_row.get("short_sl", 0)), step=0.05)
                e_stgt = st.number_input("Short TGT ₹", value=float(edit_row.get("short_tgt", 0)), step=0.05)
            with ec3:
                e_ltgt = st.number_input("Long TGT ₹", value=float(edit_row.get("long_tgt", 0)), step=0.05)
                e_inter = st.number_input("Intermediate TGT ₹", value=float(edit_row.get("intermediate", 0) or 0), step=0.05)
                e_final = st.number_input("Final TGT ₹", value=float(edit_row.get("final_tgt", 0) or 0), step=0.05)

            if st.form_submit_button("Update Position", use_container_width=True):
                idx = df[df["script"] == edit_script].index[0]
                df.at[idx, "nse_symbol"] = e_nse.strip().upper()
                df.at[idx, "qty"] = e_qty
                df.at[idx, "buy_price"] = e_buy
                df.at[idx, "long_sl"] = e_lsl
                df.at[idx, "short_sl"] = e_ssl
                df.at[idx, "short_tgt"] = e_stgt
                df.at[idx, "long_tgt"] = e_ltgt
                df.at[idx, "intermediate"] = e_inter if e_inter > 0 else np.nan
                df.at[idx, "final_tgt"] = e_final if e_final > 0 else np.nan
                save_data(df)
                st.success(f"✅ {edit_script} updated!")
                st.cache_data.clear()
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: BULK UPLOAD
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="form-card"><div class="form-title">📥 Bulk Upload via Excel / CSV</div>', unsafe_allow_html=True)

    st.markdown("""
    Upload an Excel or CSV file with these **exact column names**:

    `script` · `nse_symbol` · `qty` · `buy_price` · `long_sl` · `short_sl` · `short_tgt` · `long_tgt` · `intermediate` · `final_tgt`

    - `intermediate` and `final_tgt` are optional
    - `nse_symbol` should be NSE ticker without `.NS` (e.g. `CHAMBLFERT`)
    - Existing scripts with the same name will be **overwritten**
    """)

    uploaded = st.file_uploader("Drop Excel or CSV here", type=["xlsx", "xls", "csv"])

    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                upload_df = pd.read_csv(uploaded)
            else:
                upload_df = pd.read_excel(uploaded)

            # Normalize columns
            upload_df.columns = [c.strip().lower().replace(" ", "_") for c in upload_df.columns]

            required = ["script", "nse_symbol", "qty", "buy_price", "long_sl", "short_sl", "short_tgt", "long_tgt"]
            missing = [c for c in required if c not in upload_df.columns]

            if missing:
                st.error(f"Missing columns: {', '.join(missing)}")
            else:
                st.success(f"✅ {len(upload_df)} rows detected. Preview:")
                st.dataframe(upload_df.head(10), use_container_width=True)

                mode = st.radio("Import mode", ["Append (keep existing, add new)", "Replace all (wipe current data)"])

                if st.button("Confirm Import", type="primary"):
                    if "Replace all" in mode:
                        df = upload_df[COLUMNS if all(c in upload_df.columns for c in COLUMNS) else upload_df.columns]
                    else:
                        # Append: overwrite same scripts, add new ones
                        existing_scripts = df["script"].tolist()
                        new_rows = upload_df[~upload_df["script"].isin(existing_scripts)]
                        updated_rows = upload_df[upload_df["script"].isin(existing_scripts)]
                        for _, row in updated_rows.iterrows():
                            idx = df[df["script"] == row["script"]].index[0]
                            for col in upload_df.columns:
                                if col in df.columns:
                                    df.at[idx, col] = row[col]
                        df = pd.concat([df, new_rows], ignore_index=True)

                    save_data(df)
                    st.success(f"✅ Import complete! {len(df)} total positions.")
                    st.cache_data.clear()
                    st.rerun()

        except Exception as e:
            st.error(f"Error reading file: {e}")

    # Download template
    st.markdown("---")
    st.markdown("**📋 Download Template**")
    template_data = {
        "script": ["Chambal Fert", "Dredging Corp"],
        "nse_symbol": ["CHAMBLFERT", "DREDGECORP"],
        "qty": [5250, 1000],
        "buy_price": [445, 965],
        "long_sl": [410, 847],
        "short_sl": [415, 906],
        "short_tgt": [469, 1050],
        "long_tgt": [586, 1135],
        "intermediate": ["", ""],
        "final_tgt": [740, 1245],
    }
    template_df = pd.DataFrame(template_data)
    csv_bytes = template_df.to_csv(index=False).encode()
    st.download_button("⬇️ Download CSV Template", csv_bytes, "zigzag_template.csv", "text/csv")

    st.markdown("</div>", unsafe_allow_html=True)
