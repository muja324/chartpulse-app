import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
import ta 

# For technical indicators
from custom_ui import apply_ui
from loader import show_loader
from responsive_tabs import show_navigation

# --- Page Setup: MUST be first Streamlit call ---
st.set_page_config(page_title="ChartPulse", layout="wide")

# --- Optional Test Block ---
st.subheader("🧪 Test: Download yfinance data")
try:
    test_df = yf.download("RELIANCE.NS", period="5d", interval="15m")
    if test_df.empty:
        st.warning("⚠️ Data fetched but it's empty.")
    else:
        st.success("✅ Data downloaded successfully!")
        st.write(test_df.tail())
except Exception as e:
    st.error(f"❌ Failed to fetch data: {e}")

# --- Sidebar Settings ---
st.sidebar.header("⚙️ Settings")
symbols = st.sidebar.text_area("Stock Symbols (comma-separated)", "RELIANCE.NS, TCS.NS").split(",")
symbols = [s.strip().upper() for s in symbols if s.strip()]
show_chart = st.sidebar.checkbox("📊 Show Chart", True)
enable_alerts = st.sidebar.checkbox("📲 Telegram Alerts", False)

# --- Interval Selector ---
interval = st.selectbox("🕒 Select Interval", ["15m", "30m", "1h", "1d"], index=3)
period = "6mo" if interval == "1d" else "5d"

# --- Auto Refresh (every 1 minute) ---
REFRESH_INTERVAL = 1
st_autorefresh(interval=REFRESH_INTERVAL * 60 * 1000, key="refresh")

# --- Secrets ---
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

# --- Helper Functions ---

def fetch_data(symbol):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)

        if df.empty or df["Close"].isna().all():
            st.warning(f"No intraday data for {symbol}. Using daily fallback.")
            df = yf.download(symbol, period="1mo", interval="1d", progress=False)

        df = df.dropna(subset=["Open", "High", "Low", "Close"])
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)

        # Add technical indicators here
        df = add_technical_indicators(df)

        return df
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def add_technical_indicators(df):
    # Calculate RSI with 14 periods
    df["RSI"] = ta.momentum.rsi(df["Close"], window=14)

    # Calculate MACD
    macd_ind = ta.trend.MACD(df["Close"])
    df["MACD"] = macd_ind.macd()

    return df

def is_data_invalid(df):
    if not isinstance(df, pd.DataFrame) or df.empty:
        return True
    if any(col not in df.columns for col in ["Open", "High", "Low", "Close"]):
        return True
    if df["Close"].dropna().shape[0] < 5:
        return True
    return False

def plot_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"]
    )])
    fig.update_layout(title=f"{symbol} — {interval} Chart", height=400)
    st.plotly_chart(fig, use_container_width=True)

def send_alert(text):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text}
        )
        return response.status_code == 200
    except Exception as e:
        st.warning(f"Telegram alert error: {e}")
        return False

def safe_fmt(val, digits=2):
    try:
        return f"{val:.{digits}f}"
    except:
        return "N/A"

# --- Main Display ---

view = show_navigation()
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"🕒 Last Updated: `{now}`")

if view == "📈 Live Feed":
    for symbol in symbols:
        st.markdown(f"---\n### 🔍 {symbol}")
        show_loader(f"Fetching {symbol}...")
        df = fetch_data(symbol)

        if df.empty or any(col not in df.columns for col in ["Open", "High", "Low", "Close"]):
            st.error(f"⚠️ Signal Data Unavailable for {symbol}")
            continue

        if len(df) < 30:
            st.info(f"ℹ️ Not enough data for {symbol} (only {len(df)} rows)")
            continue

        if is_data_invalid(df):
            st.warning(f"⚠️ No valid data for {symbol}")
            continue

        apply_ui(df)

        try:
            latest = float(df["Close"].iloc[-1])
            breakout = float(df["High"].tail(20).max())
            breakdown = float(df["Low"].tail(20).min())

            rsi = float(df["RSI"].dropna().iloc[-1]) if "RSI" in df.columns and not df["RSI"].dropna().empty else None
            macd = float(df["MACD"].dropna().iloc[-1]) if "MACD" in df.columns and not df["MACD"].dropna().empty else None

            st.markdown(
                f"**Price:** ₹{safe_fmt(latest)} | "
                f"📈 BO: ₹{safe_fmt(breakout)} | "
                f"📉 BD: ₹{safe_fmt(breakdown)} | "
                f"RSI: {safe_fmt(rsi, 1)} | "
                f"MACD: {safe_fmt(macd)}"
            )

            alert = None
            if breakout is not None and latest > breakout:
                alert = f"🚀 *{symbol} Breakout!* ₹{safe_fmt(latest)} > ₹{safe_fmt(breakout)}"
            elif breakdown is not None and latest < breakdown:
                alert = f"⚠️ *{symbol} Breakdown!* ₹{safe_fmt(latest)} < ₹{safe_fmt(breakdown)}"

            if enable_alerts and alert:
                if send_alert(alert):
                    st.success("Telegram alert sent.")
                else:
                    st.warning("Alert failed.")

            if show_chart:
                plot_chart(df, symbol)

        except Exception as e:
            st.error(f"⚠️ Processing error for **{symbol}**")
            st.exception(e)
