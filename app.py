import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time
import time as time_module
import pytz
from logzero import logger
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Nifty PCR Dashboard", page_icon="📊", layout="wide")

# ─── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#0a0e1a;color:#e2e8f0;}
.stApp{background:#0a0e1a;}
.main-header{background:linear-gradient(135deg,#1a1f35,#0f172a);border:1px solid #2d3748;border-radius:12px;padding:20px 28px;margin-bottom:20px;}
.main-title{font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700;color:#38bdf8;letter-spacing:2px;margin:0;}
.subtitle{font-size:12px;color:#64748b;margin-top:4px;font-family:'JetBrains Mono',monospace;}
.metric-card{background:#111827;border:1px solid #1e293b;border-radius:10px;padding:14px 18px;text-align:center;}
.metric-label{font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1.5px;font-family:'JetBrains Mono',monospace;}
.metric-value{font-size:26px;font-weight:700;font-family:'JetBrains Mono',monospace;margin:4px 0;}
.metric-sub{font-size:11px;color:#94a3b8;font-family:'JetBrains Mono',monospace;}
.bullish{color:#22c55e;} .bearish{color:#ef4444;} .neutral{color:#f59e0b;} .sky{color:#38bdf8;}
.strike-badge{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:6px 10px;font-family:'JetBrains Mono',monospace;font-size:12px;text-align:center;margin:3px 0;}
.atm-badge{background:#172554;border:2px solid #38bdf8;color:#38bdf8;border-radius:8px;padding:6px 10px;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;text-align:center;}
.signal-box{border-radius:10px;padding:12px 18px;text-align:center;font-family:'JetBrains Mono',monospace;font-size:15px;font-weight:700;letter-spacing:1px;}
.signal-bullish{background:#052e16;border:1px solid #22c55e;color:#22c55e;}
.signal-bearish{background:#450a0a;border:1px solid #ef4444;color:#ef4444;}
.signal-neutral{background:#1c1a00;border:1px solid #f59e0b;color:#f59e0b;}
.signal-block{background:#1e1b4b;border:1px solid #818cf8;color:#818cf8;}
.section-title{font-size:11px;font-family:'JetBrains Mono',monospace;color:#64748b;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;}
.login-ok{background:#052e16;color:#22c55e;border:1px solid #22c55e;border-radius:20px;padding:5px 14px;font-family:'JetBrains Mono',monospace;font-size:12px;}
.login-err{background:#450a0a;color:#ef4444;border:1px solid #ef4444;border-radius:20px;padding:5px 14px;font-family:'JetBrains Mono',monospace;font-size:12px;}
.stButton>button{background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:8px;font-family:'JetBrains Mono',monospace;font-size:12px;}
.stButton>button:hover{border-color:#38bdf8;color:#38bdf8;}
.stTextArea textarea{background:#111827!important;color:#e2e8f0!important;border:1px solid #1e293b!important;font-family:'JetBrains Mono',monospace!important;font-size:12px!important;border-radius:8px!important;}
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ───────────────────────────────────────────────────────────────
IST          = pytz.timezone("Asia/Kolkata")
MARKET_OPEN  = time(9, 15)
SIGNAL_START = time(9, 30)
MARKET_CLOSE = time(15, 30)
REFRESH_SEC  = 30

# Nifty Top 25 Weighted Stocks
NIFTY_STOCKS = [
    {"name":"HDFC Bank",    "token":"1333",  "symbol":"HDFCBANK",   "weight":13.10},
    {"name":"Reliance",     "token":"2885",  "symbol":"RELIANCE",   "weight":9.20},
    {"name":"ICICI Bank",   "token":"4963",  "symbol":"ICICIBANK",  "weight":7.40},
    {"name":"Infosys",      "token":"1594",  "symbol":"INFY",       "weight":5.80},
    {"name":"TCS",          "token":"11536", "symbol":"TCS",        "weight":4.50},
    {"name":"Kotak Bank",   "token":"1922",  "symbol":"KOTAKBANK",  "weight":3.80},
    {"name":"L&T",          "token":"11483", "symbol":"LT",         "weight":3.60},
    {"name":"Axis Bank",    "token":"5900",  "symbol":"AXISBANK",   "weight":3.10},
    {"name":"SBI",          "token":"3045",  "symbol":"SBIN",       "weight":2.90},
    {"name":"HUL",          "token":"1394",  "symbol":"HINDUNILVR", "weight":2.70},
    {"name":"Bajaj Finance","token":"317",   "symbol":"BAJFINANCE", "weight":2.50},
    {"name":"Bharti Airtel","token":"10604", "symbol":"BHARTIARTL", "weight":2.40},
    {"name":"ITC",          "token":"1660",  "symbol":"ITC",        "weight":2.20},
    {"name":"Sun Pharma",   "token":"3351",  "symbol":"SUNPHARMA",  "weight":2.00},
    {"name":"M&M",          "token":"2031",  "symbol":"M&M",        "weight":1.90},
    {"name":"Titan",        "token":"3506",  "symbol":"TITAN",      "weight":1.80},
    {"name":"Asian Paints", "token":"236",   "symbol":"ASIANPAINT", "weight":1.70},
    {"name":"Wipro",        "token":"3787",  "symbol":"WIPRO",      "weight":1.60},
    {"name":"HCL Tech",     "token":"7229",  "symbol":"HCLTECH",    "weight":1.50},
    {"name":"NTPC",         "token":"11630", "symbol":"NTPC",       "weight":1.40},
    {"name":"Power Grid",   "token":"14977", "symbol":"POWERGRID",  "weight":1.30},
    {"name":"Nestle",       "token":"17963", "symbol":"NESTLEIND",  "weight":1.20},
    {"name":"JSW Steel",    "token":"11723", "symbol":"JSWSTEEL",   "weight":1.10},
    {"name":"Tata Motors",  "token":"3456",  "symbol":"TATAMOTORS", "weight":1.00},
    {"name":"Dr Reddy's",   "token":"881",   "symbol":"DRREDDY",    "weight":0.90},
]

# ─── SESSION STATE ───────────────────────────────────────────────────────────
for k, v in {
    "logged_in": False, "smart_api": None,
    "pcr_history": [], "stock_history": [],
    "notes": "", "last_refresh": None,
    "current_price": None, "atm": None,
    "login_time": None, "login_attempted": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── AUTO LOGIN ──────────────────────────────────────────────────────────────
def angel_login():
    try:
        from SmartApi import SmartConnect
        import pyotp
        api_key   = st.secrets["ANGEL_API_KEY"]
        client_id = st.secrets["ANGEL_CLIENT_ID"]
        password  = st.secrets["ANGEL_PASSWORD"]
        totp_key  = st.secrets.get("ANGEL_TOTP", "")
        smart = SmartConnect(api_key=api_key)
        totp  = pyotp.TOTP(totp_key).now() if totp_key else ""
        data  = smart.generateSession(client_id, password, totp)
        if data["status"]:
            st.session_state.smart_api  = smart
            st.session_state.logged_in  = True
            st.session_state.login_time = datetime.now(IST).strftime("%d-%b %H:%M")
            logger.info("Login OK")
            return True, "✅ Login Successful"
        return False, f"❌ {data.get('message','Login Failed')}"
    except KeyError as e:
        return False, f"❌ Secret missing: {e}"
    except Exception as e:
        return False, f"❌ {e}"

# Auto-login once on startup during market hours
now_ist  = datetime.now(IST)
now_time = now_ist.time()
is_market = MARKET_OPEN <= now_time <= MARKET_CLOSE
is_block  = now_time < SIGNAL_START

if is_market and not st.session_state.logged_in and not st.session_state.login_attempted:
    st.session_state.login_attempted = True
    ok, msg = angel_login()
    if not ok:
        st.session_state.login_attempted = False  # retry next refresh

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def get_nifty_price():
    try:
        d = st.session_state.smart_api.ltpData("NSE", "NIFTY", "26000")
        if d and d["status"]:
            return float(d["data"]["ltp"])
    except: pass
    return None

def get_atm(price, step=50):
    """ATM = nearest strike to current price"""
    return int(round(price / step) * step)

def get_strikes(price, step=50):
    """ATM + 4 OTM each side = 5 strikes per side"""
    atm = get_atm(price, step)
    # Call side: ATM, ATM+50, ATM+100, ATM+150, ATM+200  (ATM + 4 OTM)
    call_strikes = [atm + step*i for i in range(5)]
    # Put side:  ATM, ATM-50, ATM-100, ATM-150, ATM-200  (ATM + 4 OTM)
    put_strikes  = [atm - step*i for i in range(5)]
    return atm, call_strikes, put_strikes

def fetch_option_chain(expiry):
    smart = st.session_state.smart_api
    
    # Method 1: optionGreek API
    try:
        data = smart.optionGreek({"name":"NIFTY","expirydate":expiry})
        if data and data.get("status") and data.get("data"):
            logger.info(f"OC via optionGreek: {len(data['data'])} rows")
            return data["data"]
    except Exception as e:
        logger.warning(f"optionGreek failed: {e}")

    # Method 2: searchScrip based live feed via getMarketData
    try:
        import requests, json
        headers = {
            "Authorization": f"Bearer {smart.auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "00:00:00:00:00:00",
            "X-PrivateKey": st.secrets["ANGEL_API_KEY"],
        }
        # Get all NFO NIFTY option tokens for expiry
        url = "https://apiconnect.angelone.in/rest/secure/angelbroking/marketData/v1/optionChain"
        payload = {"name": "NIFTY", "expirydate": expiry}
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            rdata = resp.json()
            if rdata.get("status") and rdata.get("data"):
                logger.info(f"OC via REST: {len(rdata['data'])} rows")
                return rdata["data"]
    except Exception as e:
        logger.warning(f"REST OC failed: {e}")

    # Method 3: Build option chain manually from individual LTP calls
    try:
        logger.info("Building OC manually via LTP...")
        return _build_manual_oc(expiry)
    except Exception as e:
        logger.error(f"Manual OC failed: {e}")

    return []


def _build_manual_oc(expiry):
    """Build option chain manually using searchScrip + LTP for each strike"""
    smart = st.session_state.smart_api
    price = st.session_state.current_price
    if not price:
        return []

    atm = get_atm(price)
    # Generate strikes: ATM ± 10 strikes
    step = 50
    strikes = [atm + step*i for i in range(-10, 11)]

    # Convert expiry format: "30-JUN-2026" -> "30Jun2026"
    try:
        exp_dt = datetime.strptime(expiry, "%d-%b-%Y")
        exp_str = exp_dt.strftime("%d%b%Y").upper()  # "30JUN2026"
        exp_str2 = exp_dt.strftime("%-d %b %Y").upper()  # "30 JUN 2026"
    except:
        exp_str = expiry.replace("-","")

    rows = []
    for strike in strikes:
        row = {"strikePrice": strike, "callOI": 0, "putOI": 0,
               "callChgOI": 0, "putChgOI": 0, "callLTP": 0, "putLTP": 0}
        for opt_type in ["CE","PE"]:
            try:
                # Search for this option scrip
                search = smart.searchScrip("NFO", f"NIFTY{exp_str}{strike}{opt_type}")
                if search and search.get("data"):
                    token = search["data"][0]["symboltoken"]
                    ltp_data = smart.ltpData("NFO", f"NIFTY{exp_str}{strike}{opt_type}", token)
                    if ltp_data and ltp_data.get("status"):
                        d = ltp_data["data"]
                        ltp = float(d.get("ltp", 0))
                        oi  = int(float(d.get("opentInterest", 0)))
                        prev_oi = int(float(d.get("previousClose", 0)))
                        if opt_type == "CE":
                            row["callLTP"] = ltp
                            row["callOI"]  = oi
                            row["callChgOI"] = oi - prev_oi
                        else:
                            row["putLTP"] = ltp
                            row["putOI"]  = oi
                            row["putChgOI"] = oi - prev_oi
            except:
                pass
        rows.append(row)

    logger.info(f"Manual OC built: {len(rows)} strikes")
    return rows

def parse_pcr(chain_data, call_strikes, put_strikes, atm):
    if not chain_data:
        return None
    df = pd.DataFrame(chain_data)
    if df.empty:
        return None

    num_cols = ["strikePrice","callOI","putOI","callChgOI","putChgOI","callLTP","putLTP"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        else:
            df[c] = 0

    # Filter: call side + put side (unique strikes)
    all_sel = sorted(set(call_strikes + put_strikes))
    filt = df[df["strikePrice"].isin(all_sel)].copy()

    # Totals
    tc_oi  = filt["callOI"].sum()
    tp_oi  = filt["putOI"].sum()
    tc_chg = filt["callChgOI"].sum()
    tp_chg = filt["putChgOI"].sum()

    oi_pcr  = round(tp_oi  / tc_oi,  3) if tc_oi  > 0 else 0.0
    chg_pcr = round(tp_chg / tc_chg, 3) if tc_chg > 0 else 0.0

    rows = []
    for _, r in filt.sort_values("strikePrice").iterrows():
        s = int(r["strikePrice"])
        label = "ATM" if s == atm else ("OTM-C" if s > atm else "OTM-P")
        rows.append({
            "Strike": s, "Type": label,
            "Call LTP": round(r["callLTP"],2),
            "Call OI":  int(r["callOI"]),
            "Call ΔOI": int(r["callChgOI"]),
            "Put LTP":  round(r["putLTP"],2),
            "Put OI":   int(r["putOI"]),
            "Put ΔOI":  int(r["putChgOI"]),
            "OI PCR":   round(r["putOI"]  / r["callOI"],  3) if r["callOI"]  > 0 else 0,
            "ΔOI PCR":  round(r["putChgOI"] / r["callChgOI"], 3) if r["callChgOI"] > 0 else 0,
        })

    return {
        "tc_oi": tc_oi, "tp_oi": tp_oi,
        "tc_chg": tc_chg, "tp_chg": tp_chg,
        "oi_pcr": oi_pcr, "chg_pcr": chg_pcr,
        "table": pd.DataFrame(rows),
    }

def pcr_signal(val):
    if val > 1.3:   return "BULLISH 🟢", "bullish"
    if val < 0.7:   return "BEARISH 🔴", "bearish"
    return "NEUTRAL 🟡", "neutral"

def get_stock_data(top_n=25):
    results = []
    smart = st.session_state.smart_api
    for s in NIFTY_STOCKS[:top_n]:
        try:
            d = smart.ltpData("NSE", s["symbol"], s["token"])
            if d and d["status"]:
                ltp  = float(d["data"]["ltp"])
                prev = float(d["data"].get("close", ltp))
                chg  = round(((ltp - prev) / prev) * 100, 2) if prev > 0 else 0.0
                results.append({
                    "Stock": s["name"], "Symbol": s["symbol"],
                    "Weight%": s["weight"], "LTP": ltp,
                    "Chg%": chg,
                    "Wtd Chg": round(chg * s["weight"] / 100, 4),
                })
        except: pass
    return pd.DataFrame(results) if results else pd.DataFrame()

def make_pcr_chart(history):
    if not history: return None
    df = pd.DataFrame(history)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["time"], y=df["oi_pcr"],
        mode="lines+markers", name="OI PCR",
        line=dict(color="#38bdf8", width=2), marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=df["time"], y=df["chg_pcr"],
        mode="lines+markers", name="ΔOI PCR",
        line=dict(color="#f59e0b", width=2, dash="dot"), marker=dict(size=4)))
    fig.add_hline(y=1.3, line_dash="dash", line_color="#22c55e",
        annotation_text="Bullish 1.3", annotation_font_color="#22c55e")
    fig.add_hline(y=0.7, line_dash="dash", line_color="#ef4444",
        annotation_text="Bearish 0.7", annotation_font_color="#ef4444")
    fig.add_hline(y=1.0, line_dash="dot", line_color="#475569")
    fig.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        font=dict(family="JetBrains Mono", color="#94a3b8", size=11),
        legend=dict(orientation="h", y=1.12),
        margin=dict(l=10,r=10,t=30,b=10), height=300,
        xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b", title="PCR"),
        hovermode="x unified",
    )
    return fig

def make_stock_chart(history, key="wtd_avg_25"):
    if not history: return None
    df = pd.DataFrame(history)
    if key not in df.columns: return None
    colors = ["#22c55e" if v >= 0 else "#ef4444" for v in df[key]]
    fig = go.Figure(go.Bar(x=df["time"], y=df[key],
        marker_color=colors, name="Wtd Avg Chg%"))
    fig.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        font=dict(family="JetBrains Mono", color="#94a3b8", size=11),
        margin=dict(l=10,r=10,t=20,b=10), height=250,
        xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b", title="Wtd Chg%"),
        hovermode="x unified",
    )
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    st.markdown("---")

    now_s = datetime.now(IST)
    if st.session_state.logged_in:
        st.markdown(f'<span class="login-ok">🟢 Connected · {st.session_state.login_time}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="login-err">🔴 Not Connected</span>', unsafe_allow_html=True)
        if st.button("🔑 Login to Angel One", use_container_width=True):
            with st.spinner("Connecting..."):
                ok, msg = angel_login()
            st.success(msg) if ok else st.error(msg)
            if ok: st.rerun()

    st.markdown("---")
    expiry_date = st.text_input("📅 Expiry (DD-MMM-YYYY)", value="30-JUN-2026")
    auto_refresh = st.toggle("🔄 Auto Refresh 30s", value=True)
    if st.button("🔃 Refresh Now", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Notepad")
    notes = st.text_area("Trade notes:", value=st.session_state.notes, height=160,
        placeholder="Write your observations here...")
    if notes != st.session_state.notes:
        st.session_state.notes = notes

    st.markdown("---")
    st.markdown(f"""<div style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#64748b;text-align:center;">
        📅 {now_s.strftime('%d %b %Y')}<br>🕐 {now_s.strftime('%H:%M:%S')} IST</div>""",
        unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""<div class="main-header">
    <p class="main-title">📊 NIFTY PCR DASHBOARD</p>
    <p class="subtitle">Angel One Smart API · Option Chain · PCR · Live 30s</p>
</div>""", unsafe_allow_html=True)

# Market Status
now_ist  = datetime.now(IST)
now_time = now_ist.time()
if now_time < MARKET_OPEN:
    mkt_txt, mkt_col, is_block, is_market = "⏳ Market Opens at 9:15 AM", "#64748b", True, False
elif now_time < SIGNAL_START:
    mkt_txt, mkt_col, is_block, is_market = "🚫 Signal Blocked (9:15–9:30 AM)", "#818cf8", True, True
elif now_time <= MARKET_CLOSE:
    mkt_txt, mkt_col, is_block, is_market = "✅ Market Live — Signals Active", "#22c55e", False, True
else:
    mkt_txt, mkt_col, is_block, is_market = "🔒 Market Closed", "#64748b", True, False

c1, c2 = st.columns([3,1])
c1.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:13px;color:{mkt_col};padding:6px 0;">{mkt_txt}</div>', unsafe_allow_html=True)
c2.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:12px;color:#64748b;text-align:right;padding:6px 0;">{now_ist.strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

if is_block and is_market:
    st.markdown('<div class="signal-box signal-block">🚫 &nbsp; SIGNAL BLOCKED — Waiting for 9:30 AM</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ─── DATA FETCH ───────────────────────────────────────────────────────────────
pcr_data  = None
stock_df  = pd.DataFrame()
nifty_price = st.session_state.current_price
atm = st.session_state.atm

if st.session_state.logged_in and is_market and not is_block:
    price = get_nifty_price()
    if price:
        nifty_price = price
        st.session_state.current_price = price
        atm_val = get_atm(price)
        st.session_state.atm = atm_val
        atm = atm_val
        _, call_strikes, put_strikes = get_strikes(price)

        chain = fetch_option_chain(expiry_date)
        if chain:
            pcr_data = parse_pcr(chain, call_strikes, put_strikes, atm_val)
            if pcr_data:
                st.session_state.pcr_history.append({
                    "time": now_ist.strftime("%H:%M:%S"),
                    "oi_pcr": pcr_data["oi_pcr"],
                    "chg_pcr": pcr_data["chg_pcr"],
                })
                if len(st.session_state.pcr_history) > 200:
                    st.session_state.pcr_history = st.session_state.pcr_history[-200:]

        stock_df = get_stock_data(25)
        if not stock_df.empty:
            t10 = stock_df.head(10)
            t25 = stock_df.head(25)
            adv = int((stock_df["Chg%"] > 0).sum())
            dec = int((stock_df["Chg%"] < 0).sum())
            unc = int((stock_df["Chg%"] == 0).sum())
            wtd10 = round((t10["Chg%"] * t10["Weight%"]).sum() / t10["Weight%"].sum(), 3) if not t10.empty else 0
            wtd25 = round((t25["Chg%"] * t25["Weight%"]).sum() / t25["Weight%"].sum(), 3) if not t25.empty else 0
            st.session_state.stock_history.append({
                "time": now_ist.strftime("%H:%M:%S"),
                "wtd_avg_10": wtd10, "wtd_avg_25": wtd25,
                "advance": adv, "decline": dec, "unchanged": unc,
            })
            if len(st.session_state.stock_history) > 200:
                st.session_state.stock_history = st.session_state.stock_history[-200:]

        st.session_state.last_refresh = now_ist.strftime("%H:%M:%S")

elif nifty_price and atm:
    _, call_strikes, put_strikes = get_strikes(nifty_price)

# ─── TOP METRICS ─────────────────────────────────────────────────────────────
m1,m2,m3,m4,m5 = st.columns(5)

price_str = f"₹{nifty_price:,.2f}" if nifty_price else "--"
atm_str   = str(atm) if atm else "--"
oi_pcr_str  = f"{pcr_data['oi_pcr']:.3f}" if pcr_data else "--"
chg_pcr_str = f"{pcr_data['chg_pcr']:.3f}" if pcr_data else "--"
refresh_str = st.session_state.last_refresh or "--"

oi_sig_t,  oi_cls  = pcr_signal(pcr_data["oi_pcr"])  if pcr_data else ("--","neutral")
chg_sig_t, chg_cls = pcr_signal(pcr_data["chg_pcr"]) if pcr_data else ("--","neutral")

def sig_color(cls): return {"bullish":"#22c55e","bearish":"#ef4444"}.get(cls,"#f59e0b")

with m1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Nifty 50</div>
        <div class="metric-value sky">{price_str}</div>
        <div class="metric-sub">Current Price</div></div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">ATM Strike</div>
        <div class="metric-value" style="color:#a78bfa;">{atm_str}</div>
        <div class="metric-sub">Auto-tracked</div></div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">OI PCR</div>
        <div class="metric-value" style="color:{sig_color(oi_cls)};">{oi_pcr_str}</div>
        <div class="metric-sub">{oi_sig_t}</div></div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">ΔOI PCR</div>
        <div class="metric-value" style="color:{sig_color(chg_cls)};">{chg_pcr_str}</div>
        <div class="metric-sub">{chg_sig_t}</div></div>""", unsafe_allow_html=True)
with m5:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Last Refresh</div>
        <div class="metric-value" style="color:#64748b;font-size:18px;">{refresh_str}</div>
        <div class="metric-sub">Every 30 sec</div></div>""", unsafe_allow_html=True)

# ─── SIGNAL ──────────────────────────────────────────────────────────────────
st.markdown("---")
if pcr_data:
    comb = round((pcr_data["oi_pcr"] + pcr_data["chg_pcr"]) / 2, 3)
    sig_txt, sig_cls = pcr_signal(comb)
    st.markdown(f'<div class="signal-box signal-{sig_cls}">📡 &nbsp; COMBINED PCR SIGNAL: {sig_txt} &nbsp;|&nbsp; Avg PCR: {comb:.3f}</div>', unsafe_allow_html=True)

# ─── STRIKES ─────────────────────────────────────────────────────────────────
if nifty_price and atm:
    _, cs, ps = get_strikes(nifty_price)
    all_s = sorted(set(cs + ps))
    st.markdown("<br><div class='section-title'>🎯 Strikes Being Tracked (ATM + 4 OTM each side)</div>", unsafe_allow_html=True)
    cols = st.columns(len(all_s))
    for i, s in enumerate(all_s):
        with cols[i]:
            if s == atm:
                st.markdown(f'<div class="atm-badge">⭐{s}<br><small>ATM</small></div>', unsafe_allow_html=True)
            elif s > atm:
                st.markdown(f'<div class="strike-badge" style="border-color:#38bdf8;">{s}<br><small style="color:#38bdf8">CE OTM</small></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="strike-badge" style="border-color:#f59e0b;">{s}<br><small style="color:#f59e0b">PE OTM</small></div>', unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────
st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["📈 PCR Chart", "📋 Option Chain Table", "🏦 Top 25 Stocks", "📊 Advance/Decline"])

with tab1:
    if st.session_state.pcr_history:
        fig = make_pcr_chart(st.session_state.pcr_history)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        # PCR history table below chart
        st.markdown('<div class="section-title">📋 PCR History Table (Touch chart point to see)</div>', unsafe_allow_html=True)
        h_df = pd.DataFrame(st.session_state.pcr_history)
        h_df = h_df.iloc[::-1].reset_index(drop=True)  # latest first
        st.dataframe(h_df.style.format({"oi_pcr":"{:.3f}","chg_pcr":"{:.3f}"}),
            use_container_width=True, hide_index=True, height=200)
        # OI totals
        if pcr_data:
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Call OI",  f"{pcr_data['tc_oi']:,}")
            c2.metric("Total Put OI",   f"{pcr_data['tp_oi']:,}")
            c3.metric("Call ΔOI",       f"{pcr_data['tc_chg']:,}")
            c4.metric("Put ΔOI",        f"{pcr_data['tp_chg']:,}")
    else:
        st.info("⏳ PCR chart will populate after 9:30 AM...")

with tab2:
    if pcr_data and not pcr_data["table"].empty:
        tbl = pcr_data["table"].copy()
        def color_row(row):
            if row["Strike"] == atm:
                return ["background-color:#172554;color:#38bdf8"]*len(row)
            if row["Strike"] > atm:
                return ["background-color:#0f172a;color:#c7d2fe"]*len(row)
            return ["background-color:#0f1a0f;color:#bbf7d0"]*len(row)
        styled = tbl.style.apply(color_row, axis=1).format({
            "Call LTP":"₹{:.2f}","Put LTP":"₹{:.2f}",
            "Call OI":"{:,}","Put OI":"{:,}",
            "Call ΔOI":"{:,}","Put ΔOI":"{:,}",
            "OI PCR":"{:.3f}","ΔOI PCR":"{:.3f}",
        })
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.info("⏳ Option chain data will appear after 9:30 AM...")

with tab3:
    if st.session_state.stock_history:
        latest = st.session_state.stock_history[-1]
        c1,c2 = st.columns(2)
        col10 = "#22c55e" if latest["wtd_avg_10"] >= 0 else "#ef4444"
        col25 = "#22c55e" if latest["wtd_avg_25"] >= 0 else "#ef4444"
        c1.markdown(f"""<div class="metric-card">
            <div class="metric-label">Top 10 Weighted Avg</div>
            <div class="metric-value" style="color:{col10};">{latest['wtd_avg_10']:+.3f}%</div>
        </div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="metric-card">
            <div class="metric-label">Top 25 Weighted Avg</div>
            <div class="metric-value" style="color:{col25};">{latest['wtd_avg_25']:+.3f}%</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        fig_s = make_stock_chart(st.session_state.stock_history, "wtd_avg_25")
        if fig_s:
            st.plotly_chart(fig_s, use_container_width=True)

        # Stock history table
        st.markdown('<div class="section-title">📋 Stock History Table</div>', unsafe_allow_html=True)
        sh_df = pd.DataFrame(st.session_state.stock_history).iloc[::-1].reset_index(drop=True)
        st.dataframe(sh_df.style.format({
            "wtd_avg_10":"{:+.3f}%","wtd_avg_25":"{:+.3f}%",
        }), use_container_width=True, hide_index=True, height=200)

        # Current stocks table
        if not stock_df.empty:
            st.markdown('<div class="section-title">📋 Current Stock Data</div>', unsafe_allow_html=True)
            def color_chg(val):
                return "color:#22c55e" if val > 0 else ("color:#ef4444" if val < 0 else "color:#94a3b8")
            st_styled = stock_df.style\
                .map(color_chg, subset=["Chg%","Wtd Chg"])\
                .format({"LTP":"₹{:.2f}","Chg%":"{:+.2f}%","Weight%":"{:.2f}%","Wtd Chg":"{:+.4f}"})
            st.dataframe(st_styled, use_container_width=True, hide_index=True)
    else:
        st.info("⏳ Stock data will appear after 9:30 AM...")

with tab4:
    if st.session_state.stock_history:
        latest = st.session_state.stock_history[-1]
        adv, dec, unc = latest["advance"], latest["decline"], latest["unchanged"]
        total = adv + dec + unc

        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(f"""<div class="metric-card">
            <div class="metric-label">Advancing</div>
            <div class="metric-value bullish">{adv}</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="metric-card">
            <div class="metric-label">Declining</div>
            <div class="metric-value bearish">{dec}</div></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="metric-card">
            <div class="metric-label">Unchanged</div>
            <div class="metric-value neutral">{unc}</div></div>""", unsafe_allow_html=True)
        c4.markdown(f"""<div class="metric-card">
            <div class="metric-label">A/D Ratio</div>
            <div class="metric-value sky">{adv}/{dec}</div></div>""", unsafe_allow_html=True)

        # A/D Bar chart over time
        if len(st.session_state.stock_history) > 1:
            sh = pd.DataFrame(st.session_state.stock_history)
            fig_ad = go.Figure()
            fig_ad.add_trace(go.Bar(x=sh["time"], y=sh["advance"], name="Advance",
                marker_color="#22c55e"))
            fig_ad.add_trace(go.Bar(x=sh["time"], y=-sh["decline"], name="Decline",
                marker_color="#ef4444"))
            fig_ad.update_layout(
                paper_bgcolor="#111827", plot_bgcolor="#111827", barmode="relative",
                font=dict(family="JetBrains Mono",color="#94a3b8",size=11),
                margin=dict(l=10,r=10,t=20,b=10), height=280,
                xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b",title="Stocks"),
                legend=dict(orientation="h",y=1.1),
            )
            st.plotly_chart(fig_ad, use_container_width=True)

        # Current bar chart
        if not stock_df.empty:
            fig_bar = go.Figure(go.Bar(
                x=stock_df["Stock"], y=stock_df["Chg%"],
                marker_color=["#22c55e" if v > 0 else "#ef4444" for v in stock_df["Chg%"]],
            ))
            fig_bar.update_layout(
                paper_bgcolor="#111827", plot_bgcolor="#111827",
                font=dict(family="JetBrains Mono",color="#94a3b8",size=10),
                margin=dict(l=10,r=10,t=10,b=80), height=300,
                xaxis=dict(gridcolor="#1e293b",tickangle=-45),
                yaxis=dict(gridcolor="#1e293b",title="Chg%"),
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("⏳ Advance/Decline data will appear after 9:30 AM...")

# ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
if auto_refresh and is_market and not is_block and st.session_state.logged_in:
    time_module.sleep(REFRESH_SEC)
    st.rerun()
