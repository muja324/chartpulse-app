import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from custom_ui import apply_ui
from responsive_tabs import show_navigation
from loader import show_loader

# --- Page config ---
st.set_page_config(page_title="ChartPulse", layout="wide")
st.title("📈 ChartPulse — Live Stock Signal Tracker")

# --- Sidebar settings ---
st.sidebar.header("⚙️ Settings")
symbols = st.sidebar.text_area("Enter Stock Symbols (comma-separated)", "RELIANCE.NS, TCS.NS").split(",")
symbols = [s.strip().upper() for s in symbols if s.strip()]

show_chart = st.sidebar.checkbox("📊 Show Candlestick Chart", True)
enable_alerts = st.sidebar.checkbox("📲 Send Telegram Alerts", False)

# --- Timeframe selector ---
interval = st.selectbox(
    "🕒 Select Interval",
    ["15m", "30m", "1h", "1d"],
    index=3,
    help="Choose timeframe for price chart & signal analysis"
)

# --- Period selection ---
period = "6mo" if interval == "1d" else "5d"

# --- Auto-refresh ---
REFRESH_INTERVAL = 1  # in minutes
st_autorefresh(interval=REFRESH_INTERVAL * 60 * 1000, key="autorefresh")

# --- Telegram secrets (optional) ---
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

# --- Helper Functions ---
def fetch_data(symbol):
    try:
        return yf.download(symbol, period=period, interval=interval, progress=False)
    except:
        return pd.DataFrame()

def is_data_invalid(df):
    return df.empty or "Close" not in df.columns or df["Close"].isnull().all()

def plot_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"]
    )])
    fig.update_layout(title=f"{symbol} - {interval} Chart", height=400)
    st.plotly_chart(fig, use_container_width=True)

def send_alert(text):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        return requests.post(url, data=data).status_code == 200
    except:
        return False

def safe_fmt(val, digits=2):
    try:
        return f"{val:.{digits}f}"
    except:
        return "N/A"

# --- Main Display ---
view = show_navigation()
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"🕒 Last updated: `{now}`")

if view == "📈 Live Feed":
    for symbol in symbols:
        st.markdown(f"---\n### 🔍 {symbol}")
        show_loader(f"Fetching {symbol}...")
        df = fetch_data(symbol)

        if is_data_invalid(df):
            st.warning(f"⚠️ No valid data for {symbol}")
            continue

        apply_ui(df)

        latest = df["Close"].iloc[-1]
        breakout = df["High"].tail(20).max()
        breakdown = df["Low"].tail(20).min()
        rsi = df.get("RSI", pd.Series()).iloc[-1] if "RSI" in df else None

        st.markdown(
            f"**Price:** ₹{safe_fmt(latest)} | "
            f"📈 BO: ₹{safe_fmt(breakout)} | "
            f"📉 BD: ₹{safe_fmt(breakdown)} | "
            f"RSI: {safe_fmt(rsi,1)}"
        )

        # Alert Logic
        alert = None
        if latest > breakout:
            alert = f"🚀 *{symbol} Breakout!* ₹{safe_fmt(latest)} > ₹{safe_fmt(breakout)}"
        elif latest < breakdown:
            alert = f"⚠️ *{symbol} Breakdown!* ₹{safe_fmt(latest)} < ₹{safe_fmt(breakdown)}"

        if enable_alerts and alert:
            if send_alert(alert):
                st.success("Telegram alert sent.")
            else:
                st.warning("Failed to send alert.")

        if show_chart:
            try:
                plot_chart(df, symbol)
            except Exception as e:
                st.error(f"Chart error: {e}")
