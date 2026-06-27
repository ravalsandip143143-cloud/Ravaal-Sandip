import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time
import time as time_module
import pytz
import json
from SmartApi import SmartConnect
from logzero import logger
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nifty PCR Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0a0e1a;
        color: #e2e8f0;
    }
    .stApp { background-color: #0a0e1a; }

    .main-header {
        background: linear-gradient(135deg, #1a1f35 0%, #0f172a 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 20px;
    }
    .main-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 26px;
        font-weight: 700;
        color: #38bdf8;
        letter-spacing: 2px;
        margin: 0;
    }
    .subtitle {
        font-size: 13px;
        color: #64748b;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }

    .metric-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
        transition: border-color 0.3s;
    }
    .metric-card:hover { border-color: #38bdf8; }
    .metric-label {
        font-size: 11px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        margin: 4px 0;
    }
    .metric-sub {
        font-size: 12px;
        color: #94a3b8;
        font-family: 'JetBrains Mono', monospace;
    }

    .bullish { color: #22c55e; }
    .bearish { color: #ef4444; }
    .neutral { color: #f59e0b; }
    .sky { color: #38bdf8; }

    .strike-badge {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 8px 14px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        text-align: center;
        margin: 3px 0;
    }
    .atm-badge {
        background: #172554;
        border: 1px solid #38bdf8;
        color: #38bdf8;
        border-radius: 8px;
        padding: 8px 14px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 700;
        text-align: center;
    }

    .signal-box {
        border-radius: 10px;
        padding: 14px 20px;
        text-align: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .signal-bullish { background: #052e16; border: 1px solid #22c55e; color: #22c55e; }
    .signal-bearish { background: #450a0a; border: 1px solid #ef4444; color: #ef4444; }
    .signal-neutral { background: #1c1a00; border: 1px solid #f59e0b; color: #f59e0b; }
    .signal-block   { background: #1e1b4b; border: 1px solid #818cf8; color: #818cf8; }

    .notepad-box {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
    }
    .section-title {
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }
    .login-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        padding: 6px 14px;
        border-radius: 20px;
        display: inline-block;
    }
    .login-ok  { background: #052e16; color: #22c55e; border: 1px solid #22c55e; }
    .login-err { background: #450a0a; color: #ef4444; border: 1px solid #ef4444; }

    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
    .stButton > button {
        background: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        padding: 6px 16px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: #38bdf8;
        color: #38bdf8;
    }
    .stTextArea textarea {
        background: #111827 !important;
        color: #e2e8f0 !important;
        border: 1px solid #1e293b !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 13px !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ───────────────────────────────────────────────────────────────
IST = pytz.timezone("Asia/Kolkata")
NIFTY_SYMBOL = "NIFTY"
NIFTY_TOKEN  = "26000"
EXCHANGE     = "NSE"
MARKET_OPEN  = time(9, 15)
SIGNAL_START = time(9, 30)
MARKET_CLOSE = time(15, 30)
REFRESH_SEC  = 30

# Nifty Top 25 Weighted Stocks (approximate weights as of 2025-26)
NIFTY_STOCKS = {
    "HDFC Bank":       {"token": "1333",  "symbol": "HDFCBANK",   "weight": 13.10},
    "Reliance":        {"token": "2885",  "symbol": "RELIANCE",   "weight": 9.20},
    "ICICI Bank":      {"token": "4963",  "symbol": "ICICIBANK",  "weight": 7.40},
    "Infosys":         {"token": "1594",  "symbol": "INFY",       "weight": 5.80},
    "TCS":             {"token": "11536", "symbol": "TCS",        "weight": 4.50},
    "Kotak Bank":      {"token": "1922",  "symbol": "KOTAKBANK",  "weight": 3.80},
    "L&T":             {"token": "11483", "symbol": "LT",         "weight": 3.60},
    "Axis Bank":       {"token": "5900",  "symbol": "AXISBANK",   "weight": 3.10},
    "SBI":             {"token": "3045",  "symbol": "SBIN",       "weight": 2.90},
    "HUL":             {"token": "1394",  "symbol": "HINDUNILVR", "weight": 2.70},
    "Bajaj Finance":   {"token": "317",   "symbol": "BAJFINANCE", "weight": 2.50},
    "Bharti Airtel":   {"token": "10604", "symbol": "BHARTIARTL", "weight": 2.40},
    "ITC":             {"token": "1660",  "symbol": "ITC",        "weight": 2.20},
    "Sun Pharma":      {"token": "3351",  "symbol": "SUNPHARMA",  "weight": 2.00},
    "M&M":             {"token": "2031",  "symbol": "M&M",        "weight": 1.90},
    "Titan":           {"token": "3506",  "symbol": "TITAN",      "weight": 1.80},
    "Asian Paints":    {"token": "236",   "symbol": "ASIANPAINT", "weight": 1.70},
    "Wipro":           {"token": "3787",  "symbol": "WIPRO",      "weight": 1.60},
    "HCL Tech":        {"token": "7229",  "symbol": "HCLTECH",    "weight": 1.50},
    "NTPC":            {"token": "11630", "symbol": "NTPC",       "weight": 1.40},
    "Power Grid":      {"token": "14977", "symbol": "POWERGRID",  "weight": 1.30},
    "Nestle":          {"token": "17963", "symbol": "NESTLEIND",  "weight": 1.20},
    "JSW Steel":       {"token": "11723", "symbol": "JSWSTEEL",   "weight": 1.10},
    "Tata Motors":     {"token": "3456",  "symbol": "TATAMOTORS", "weight": 1.00},
    "Dr Reddy's":      {"token": "881",   "symbol": "DRREDDY",    "weight": 0.90},
}

# ─── SESSION STATE INIT ──────────────────────────────────────────────────────
def init_state():
    defaults = {
        "logged_in": False,
        "smart_api": None,
        "auth_token": None,
        "feed_token": None,
        "pcr_history": [],        # list of dicts: {time, oi_pcr, chg_pcr}
        "notes": "",
        "last_refresh": None,
        "current_price": None,
        "strikes_used": [],
        "login_time": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── ANGEL ONE LOGIN ────────────────────────────────────────────────────────
def angel_login():
    try:
        api_key   = st.secrets["ANGEL_API_KEY"]
        client_id = st.secrets["ANGEL_CLIENT_ID"]
        password  = st.secrets["ANGEL_PASSWORD"]
        totp_key  = st.secrets.get("ANGEL_TOTP", "")

        smart = SmartConnect(api_key=api_key)

        if totp_key:
            import pyotp
            totp = pyotp.TOTP(totp_key).now()
        else:
            totp = ""

        data = smart.generateSession(client_id, password, totp)
        if data["status"]:
            st.session_state.smart_api  = smart
            st.session_state.auth_token = data["data"]["jwtToken"]
            st.session_state.feed_token = data["data"]["feedToken"]
            st.session_state.logged_in  = True
            st.session_state.login_time = datetime.now(IST).strftime("%d-%b-%Y %H:%M:%S")
            logger.info("Angel One login successful")
            return True, "✅ Login Successful"
        else:
            return False, f"❌ Login Failed: {data.get('message','Unknown')}"
    except KeyError as e:
        return False, f"❌ Secret missing: {e}"
    except Exception as e:
        return False, f"❌ Error: {e}"

# ─── GET NIFTY SPOT PRICE ───────────────────────────────────────────────────
def get_nifty_price():
    try:
        smart = st.session_state.smart_api
        data = smart.ltpData(EXCHANGE, NIFTY_SYMBOL, NIFTY_TOKEN)
        if data["status"]:
            return float(data["data"]["ltp"])
    except Exception as e:
        logger.error(f"Price fetch error: {e}")
    return None

# ─── GET STRIKE PRICES ──────────────────────────────────────────────────────
def get_strikes(current_price, step=50):
    """1 ITM + ATM + 4 OTM for both Call and Put"""
    atm = round(current_price / step) * step
    # Call side: 1 ITM, ATM, 4 OTM  → [atm-50, atm, atm+50, atm+100, atm+150, atm+200] but we need 1 ITM + 4 OTM = 5
    # Put  side: 1 ITM, ATM, 4 OTM
    # As per strategy: 1 ITM + 4 OTM = 5 strikes each side
    call_strikes = [atm - step] + [atm + step*i for i in range(0, 4)]   # 1 ITM + 4 OTM
    put_strikes  = [atm + step] + [atm - step*i for i in range(0, 4)]   # 1 ITM + 4 OTM (mirror)
    # Unique sorted
    all_strikes = sorted(set(call_strikes + put_strikes))
    return atm, all_strikes, call_strikes, put_strikes

# ─── FETCH OPTION CHAIN ─────────────────────────────────────────────────────
def fetch_option_chain(expiry_date=None):
    """Fetch Nifty option chain via Angel One API"""
    try:
        smart = st.session_state.smart_api
        params = {"name": "NIFTY", "expirydate": expiry_date}
        data = smart.optionGreek(params)
        if data and data.get("status"):
            return data.get("data", [])
    except Exception as e:
        logger.error(f"Option chain error: {e}")
    return []

# ─── PARSE OPTION CHAIN → PCR ───────────────────────────────────────────────
def parse_pcr(chain_data, call_strikes, put_strikes):
    """Extract OI and Change in OI for selected strikes, compute PCR"""
    chain_df = pd.DataFrame(chain_data)
    if chain_df.empty:
        return None

    # Normalize
    chain_df["strikePrice"] = pd.to_numeric(chain_df.get("strikePrice", 0), errors="coerce")
    chain_df["callOI"]      = pd.to_numeric(chain_df.get("callOI", 0),      errors="coerce").fillna(0)
    chain_df["putOI"]       = pd.to_numeric(chain_df.get("putOI", 0),       errors="coerce").fillna(0)
    chain_df["callChgOI"]   = pd.to_numeric(chain_df.get("callChgOI", 0),   errors="coerce").fillna(0)
    chain_df["putChgOI"]    = pd.to_numeric(chain_df.get("putChgOI", 0),    errors="coerce").fillna(0)
    chain_df["callLTP"]     = pd.to_numeric(chain_df.get("callLTP", 0),     errors="coerce").fillna(0)
    chain_df["putLTP"]      = pd.to_numeric(chain_df.get("putLTP", 0),      errors="coerce").fillna(0)

    selected_strikes = sorted(set(call_strikes + put_strikes))
    filtered = chain_df[chain_df["strikePrice"].isin(selected_strikes)]

    total_call_oi     = filtered["callOI"].sum()
    total_put_oi      = filtered["putOI"].sum()
    total_call_chg_oi = filtered["callChgOI"].sum()
    total_put_chg_oi  = filtered["putChgOI"].sum()

    oi_pcr  = round(total_put_oi      / total_call_oi,      3) if total_call_oi      > 0 else 0
    chg_pcr = round(total_put_chg_oi  / total_call_chg_oi,  3) if total_call_chg_oi  > 0 else 0

    rows = []
    for _, row in filtered.sort_values("strikePrice").iterrows():
        rows.append({
            "Strike": int(row["strikePrice"]),
            "Call LTP": row["callLTP"],
            "Call OI": int(row["callOI"]),
            "Call ΔOI": int(row["callChgOI"]),
            "Put LTP": row["putLTP"],
            "Put OI": int(row["putOI"]),
            "Put ΔOI": int(row["putChgOI"]),
            "PCR (OI)": round(row["putOI"]  / row["callOI"],  3) if row["callOI"]  > 0 else 0,
            "PCR (ΔOI)": round(row["putChgOI"] / row["callChgOI"], 3) if row["callChgOI"] > 0 else 0,
        })

    return {
        "total_call_oi": total_call_oi,
        "total_put_oi":  total_put_oi,
        "total_call_chg": total_call_chg_oi,
        "total_put_chg":  total_put_chg_oi,
        "oi_pcr":  oi_pcr,
        "chg_pcr": chg_pcr,
        "table":   pd.DataFrame(rows),
    }

# ─── PCR SIGNAL ──────────────────────────────────────────────────────────────
def pcr_signal(pcr_val):
    if pcr_val > 1.3:   return "BULLISH 🟢", "bullish"
    elif pcr_val < 0.7: return "BEARISH 🔴", "bearish"
    else:               return "NEUTRAL 🟡", "neutral"

# ─── STOCK CHANGE (LTP) ─────────────────────────────────────────────────────
def get_stock_changes(top_n=25):
    """Fetch LTP for top N nifty stocks, compute weighted change%"""
    try:
        smart = st.session_state.smart_api
        stocks = list(NIFTY_STOCKS.items())[:top_n]
        results = []
        for name, info in stocks:
            try:
                d = smart.ltpData("NSE", info["symbol"], info["token"])
                if d and d["status"]:
                    ltp  = float(d["data"]["ltp"])
                    prev = float(d["data"].get("close", ltp))
                    chg  = round(((ltp - prev) / prev) * 100, 2) if prev > 0 else 0.0
                    results.append({
                        "Stock": name,
                        "Symbol": info["symbol"],
                        "Weight%": info["weight"],
                        "LTP": ltp,
                        "Chg%": chg,
                        "Weighted Chg": round(chg * info["weight"] / 100, 4),
                    })
            except:
                pass
        return pd.DataFrame(results)
    except Exception as e:
        logger.error(f"Stock fetch error: {e}")
        return pd.DataFrame()

# ─── PCR CHART ───────────────────────────────────────────────────────────────
def pcr_chart(history):
    if not history:
        return None
    df = pd.DataFrame(history)
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Scatter(
        x=df["time"], y=df["oi_pcr"],
        mode="lines+markers", name="OI PCR",
        line=dict(color="#38bdf8", width=2),
        marker=dict(size=5, color="#38bdf8"),
    ))
    fig.add_trace(go.Scatter(
        x=df["time"], y=df["chg_pcr"],
        mode="lines+markers", name="ΔOI PCR",
        line=dict(color="#f59e0b", width=2, dash="dot"),
        marker=dict(size=5, color="#f59e0b"),
    ))
    fig.add_hline(y=1.3, line_dash="dash", line_color="#22c55e", annotation_text="Bullish 1.3")
    fig.add_hline(y=0.7, line_dash="dash", line_color="#ef4444", annotation_text="Bearish 0.7")
    fig.add_hline(y=1.0, line_dash="dot",  line_color="#64748b")
    fig.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        font=dict(family="JetBrains Mono", color="#94a3b8", size=11),
        legend=dict(orientation="h", y=1.1, font=dict(size=11)),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor="#1e293b", showgrid=True),
        yaxis=dict(gridcolor="#1e293b", showgrid=True, title="PCR"),
        height=320,
    )
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    st.markdown("---")

    # Login status
    if st.session_state.logged_in:
        st.markdown(f'<span class="login-status login-ok">🟢 Connected — {st.session_state.login_time}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="login-status login-err">🔴 Not Connected</span>', unsafe_allow_html=True)
        if st.button("🔑 Login to Angel One", use_container_width=True):
            with st.spinner("Connecting..."):
                ok, msg = angel_login()
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")
    expiry_date = st.text_input("📅 Expiry Date (DD-MMM-YYYY)", value="03-JUL-2025")

    auto_refresh = st.toggle("🔄 Auto Refresh (30s)", value=True)

    if st.button("🔃 Refresh Now", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Notepad")
    notes_input = st.text_area(
        "Your trade notes:",
        value=st.session_state.notes,
        height=180,
        placeholder="Write your observations here..."
    )
    if notes_input != st.session_state.notes:
        st.session_state.notes = notes_input

    # Date & Time
    st.markdown("---")
    now_ist = datetime.now(IST)
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#64748b;text-align:center;">
        📅 {now_ist.strftime('%d %b %Y')}<br>
        🕐 {now_ist.strftime('%H:%M:%S')} IST
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div class="main-header">
    <p class="main-title">📊 NIFTY PCR DASHBOARD</p>
    <p class="subtitle">Angel One Smart API · Option Chain · PCR Analysis · Live</p>
</div>
""", unsafe_allow_html=True)

# ─── Market Status ───────────────────────────────────────────────────────────
now_ist  = datetime.now(IST)
now_time = now_ist.time()

if now_time < MARKET_OPEN:
    mkt_status = "⏳ Market Closed"
    mkt_color  = "#64748b"
    is_block   = True
    is_market  = False
elif MARKET_OPEN <= now_time < SIGNAL_START:
    mkt_status = "🚫 Signal Blocked (9:15–9:30)"
    mkt_color  = "#818cf8"
    is_block   = True
    is_market  = True
elif SIGNAL_START <= now_time <= MARKET_CLOSE:
    mkt_status = "✅ Market Live — Signals Active"
    mkt_color  = "#22c55e"
    is_block   = False
    is_market  = True
else:
    mkt_status = "🔒 Market Closed"
    mkt_color  = "#64748b"
    is_block   = True
    is_market  = False

col_s1, col_s2 = st.columns([3, 1])
with col_s1:
    st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:14px;color:{mkt_color};padding:8px 0;">{mkt_status}</div>', unsafe_allow_html=True)
with col_s2:
    st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:13px;color:#64748b;text-align:right;padding:8px 0;">{now_ist.strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

# ─── Block Signal ────────────────────────────────────────────────────────────
if is_block and is_market:
    st.markdown("""
    <div class="signal-box signal-block" style="margin-bottom:20px;">
        🚫 &nbsp; SIGNAL BLOCKED — Waiting for 9:30 AM
    </div>
    """, unsafe_allow_html=True)

# ─── Main Data Fetch ─────────────────────────────────────────────────────────
pcr_data   = None
stock_df   = pd.DataFrame()
nifty_price = None

if st.session_state.logged_in and is_market and not is_block:
    # Fetch Nifty price
    nifty_price = get_nifty_price()
    if nifty_price:
        st.session_state.current_price = nifty_price
        atm, all_strikes, call_strikes, put_strikes = get_strikes(nifty_price)
        st.session_state.strikes_used = all_strikes

        # Fetch option chain
        chain = fetch_option_chain(expiry_date)
        if chain:
            pcr_data = parse_pcr(chain, call_strikes, put_strikes)
            if pcr_data:
                # Append to PCR history
                st.session_state.pcr_history.append({
                    "time":    now_ist.strftime("%H:%M:%S"),
                    "oi_pcr":  pcr_data["oi_pcr"],
                    "chg_pcr": pcr_data["chg_pcr"],
                })
                # Keep last 100 points
                if len(st.session_state.pcr_history) > 100:
                    st.session_state.pcr_history = st.session_state.pcr_history[-100:]

        # Fetch stock data (top 25)
        stock_df = get_stock_changes(top_n=25)
        st.session_state.last_refresh = now_ist.strftime("%H:%M:%S")

elif st.session_state.current_price:
    nifty_price = st.session_state.current_price
    atm, all_strikes, call_strikes, put_strikes = get_strikes(nifty_price)

# ─── TOP METRICS ─────────────────────────────────────────────────────────────
st.markdown("---")
m1, m2, m3, m4, m5 = st.columns(5)

price_display  = f"₹{nifty_price:,.2f}" if nifty_price else "--"
oi_pcr_display = f"{pcr_data['oi_pcr']:.3f}" if pcr_data else "--"
chg_pcr_display = f"{pcr_data['chg_pcr']:.3f}" if pcr_data else "--"
atm_display    = f"{int(round(nifty_price/50)*50)}" if nifty_price else "--"
refresh_time   = st.session_state.last_refresh or "--"

oi_sig_text, oi_sig_class = pcr_signal(pcr_data["oi_pcr"]) if pcr_data else ("--", "neutral")
chg_sig_text, chg_sig_class = pcr_signal(pcr_data["chg_pcr"]) if pcr_data else ("--", "neutral")

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Nifty 50</div>
        <div class="metric-value sky">{price_display}</div>
        <div class="metric-sub">Current Price</div>
    </div>""", unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">ATM Strike</div>
        <div class="metric-value" style="color:#a78bfa;">{atm_display}</div>
        <div class="metric-sub">Auto-tracked</div>
    </div>""", unsafe_allow_html=True)

with m3:
    color = "#22c55e" if oi_sig_class == "bullish" else "#ef4444" if oi_sig_class == "bearish" else "#f59e0b"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">OI PCR</div>
        <div class="metric-value" style="color:{color};">{oi_pcr_display}</div>
        <div class="metric-sub">{oi_sig_text}</div>
    </div>""", unsafe_allow_html=True)

with m4:
    color2 = "#22c55e" if chg_sig_class == "bullish" else "#ef4444" if chg_sig_class == "bearish" else "#f59e0b"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">ΔOI PCR</div>
        <div class="metric-value" style="color:{color2};">{chg_pcr_display}</div>
        <div class="metric-sub">{chg_sig_text}</div>
    </div>""", unsafe_allow_html=True)

with m5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Last Refresh</div>
        <div class="metric-value" style="color:#64748b;font-size:20px;">{refresh_time}</div>
        <div class="metric-sub">Every 30 sec</div>
    </div>""", unsafe_allow_html=True)

# ─── SIGNAL BOX ──────────────────────────────────────────────────────────────
st.markdown("---")
if pcr_data:
    combined_pcr = (pcr_data["oi_pcr"] + pcr_data["chg_pcr"]) / 2
    sig_text, sig_class = pcr_signal(combined_pcr)
    st.markdown(f"""
    <div class="signal-box signal-{sig_class}">
        📡 &nbsp; COMBINED PCR SIGNAL: {sig_text} &nbsp;|&nbsp; Avg PCR: {combined_pcr:.3f}
    </div>""", unsafe_allow_html=True)

# ─── STRIKES BEING TRACKED ───────────────────────────────────────────────────
if nifty_price:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎯 Strikes Being Tracked</div>', unsafe_allow_html=True)
    atm_val = int(round(nifty_price / 50) * 50)
    strike_cols = st.columns(len(st.session_state.strikes_used) if st.session_state.strikes_used else 5)
    for i, strike in enumerate(sorted(st.session_state.strikes_used)):
        with strike_cols[i % len(strike_cols)]:
            if strike == atm_val:
                st.markdown(f'<div class="atm-badge">⭐ {strike}<br><small>ATM</small></div>', unsafe_allow_html=True)
            else:
                label = "ITM" if strike < atm_val else "OTM"
                st.markdown(f'<div class="strike-badge">{strike}<br><small style="color:#64748b">{label}</small></div>', unsafe_allow_html=True)

# ─── PCR CHART + TABLE ───────────────────────────────────────────────────────
st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["📈 PCR Chart", "📋 Option Chain Table", "🏦 Top 25 Stocks", "📊 Advance/Decline"])

with tab1:
    if st.session_state.pcr_history:
        fig = pcr_chart(st.session_state.pcr_history)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        # OI Summary
        if pcr_data:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Call OI",  f"{pcr_data['total_call_oi']:,}")
            c2.metric("Total Put OI",   f"{pcr_data['total_put_oi']:,}")
            c3.metric("Total Call ΔOI", f"{pcr_data['total_call_chg']:,}")
            c4.metric("Total Put ΔOI",  f"{pcr_data['total_put_chg']:,}")
    else:
        st.info("⏳ PCR chart will populate after 9:30 AM when data starts flowing...")

with tab2:
    if pcr_data and not pcr_data["table"].empty:
        df_show = pcr_data["table"].copy()
        atm_val = int(round(nifty_price / 50) * 50) if nifty_price else 0

        def highlight_atm(row):
            if row["Strike"] == atm_val:
                return ["background-color: #172554; color: #38bdf8"] * len(row)
            return [""] * len(row)

        styled = df_show.style.apply(highlight_atm, axis=1)\
            .format({
                "Call LTP": "₹{:.2f}", "Put LTP": "₹{:.2f}",
                "Call OI":  "{:,}",    "Put OI":  "{:,}",
                "Call ΔOI": "{:,}",    "Put ΔOI": "{:,}",
                "PCR (OI)": "{:.3f}",  "PCR (ΔOI)": "{:.3f}",
            })
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.info("⏳ Option chain data will appear after 9:30 AM...")

with tab3:
    if not stock_df.empty:
        top10 = stock_df.head(10)
        top25 = stock_df.head(25)
        wt_avg_10 = round((top10["Chg%"] * top10["Weight%"]).sum() / top10["Weight%"].sum(), 3)
        wt_avg_25 = round((top25["Chg%"] * top25["Weight%"]).sum() / top25["Weight%"].sum(), 3)

        c1, c2 = st.columns(2)
        color10 = "#22c55e" if wt_avg_10 >= 0 else "#ef4444"
        color25 = "#22c55e" if wt_avg_25 >= 0 else "#ef4444"
        c1.markdown(f"""<div class="metric-card">
            <div class="metric-label">Top 10 Weighted Avg Chg</div>
            <div class="metric-value" style="color:{color10};">{wt_avg_10:+.3f}%</div>
        </div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="metric-card">
            <div class="metric-label">Top 25 Weighted Avg Chg</div>
            <div class="metric-value" style="color:{color25};">{wt_avg_25:+.3f}%</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        def color_chg(val):
            color = "#22c55e" if val > 0 else "#ef4444" if val < 0 else "#94a3b8"
            return f"color: {color}"

        styled_stocks = stock_df.style\
            .applymap(color_chg, subset=["Chg%", "Weighted Chg"])\
            .format({"LTP": "₹{:.2f}", "Chg%": "{:+.2f}%", "Weight%": "{:.2f}%", "Weighted Chg": "{:+.4f}"})
        st.dataframe(styled_stocks, use_container_width=True, hide_index=True)
    else:
        st.info("⏳ Stock data will appear after market open...")

with tab4:
    if not stock_df.empty:
        advance = (stock_df["Chg%"] > 0).sum()
        decline = (stock_df["Chg%"] < 0).sum()
        unchanged = (stock_df["Chg%"] == 0).sum()
        total = len(stock_df)

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"""<div class="metric-card">
            <div class="metric-label">Advancing</div>
            <div class="metric-value bullish">{advance}</div>
        </div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="metric-card">
            <div class="metric-label">Declining</div>
            <div class="metric-value bearish">{decline}</div>
        </div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="metric-card">
            <div class="metric-label">Unchanged</div>
            <div class="metric-value neutral">{unchanged}</div>
        </div>""", unsafe_allow_html=True)
        c4.markdown(f"""<div class="metric-card">
            <div class="metric-label">A/D Ratio</div>
            <div class="metric-value sky">{advance}/{decline}</div>
        </div>""", unsafe_allow_html=True)

        # Advance/Decline Bar chart
        fig_ad = go.Figure()
        fig_ad.add_bar(x=stock_df["Stock"], y=stock_df["Chg%"],
            marker_color=["#22c55e" if v > 0 else "#ef4444" for v in stock_df["Chg%"]],
            name="Change %")
        fig_ad.update_layout(
            paper_bgcolor="#111827", plot_bgcolor="#111827",
            font=dict(family="JetBrains Mono", color="#94a3b8", size=10),
            margin=dict(l=10, r=10, t=10, b=80),
            xaxis=dict(gridcolor="#1e293b", tickangle=-45),
            yaxis=dict(gridcolor="#1e293b", title="Change %"),
            height=320,
        )
        st.plotly_chart(fig_ad, use_container_width=True)
    else:
        st.info("⏳ Advance/Decline data will appear after market open...")

# ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
if auto_refresh and is_market and not is_block and st.session_state.logged_in:
    time_module.sleep(REFRESH_SEC)
    st.rerun()
