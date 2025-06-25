import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime
from custom_ui import apply_ui
apply_ui()
# Secrets
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")
REFRESH_INTERVAL = int(st.secrets.get("REFRESH_INTERVAL", 5))

# Auto-refresh
st_autorefresh(interval=REFRESH_INTERVAL * 60 * 1000, key="refresh")

# UI
st.set_page_config(page_title="ChartPulse", layout="wide")
st.title("📈 ChartPulse — Live Stock Signal Tracker")
st.sidebar.header("⚙️ Settings")

symbols = st.sidebar.text_area("Enter Stock Symbols", "RELIANCE.NS, ASTERDM.NS").split(",")
symbols = [s.strip().upper() for s in symbols if s.strip()]
show_chart = st.sidebar.checkbox("📊 Show Chart", True)
enable_alerts = st.sidebar.checkbox("📲 Telegram Alerts", True)

def fetch_data(symbol):
    try:
        return yf.download(symbol, period="5d", interval="15m")
    except:
        return pd.DataFrame()

def is_data_invalid(df):
    if df.empty:
        return True
    close = df.get("Close")
    if close is None:
        return True
    try:
        return bool(close.isnull().all())
    except:
        return True

def indicators(df):
    df["RSI"] = df["Close"].rolling(14).apply(
        lambda x: 100 - (100 / (1 + (x.diff().clip(lower=0).sum() / x.diff().clip(upper=0).abs().sum())))
        if x.diff().clip(upper=0).abs().sum() != 0 else None
    )
    exp1 = df["Close"].ewm(span=12).mean()
    exp2 = df["Close"].ewm(span=26).mean()
    df["MACD"] = exp1 - exp2
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    return df

def plot_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"]
    )])
    fig.update_layout(title=f"{symbol} - 15 Min Chart", height=400)
    st.plotly_chart(fig, use_container_width=True)

def send_alert(text):
    if not BOT_TOKEN or not CHAT_ID:
        st.warning("⚠️ Telegram credentials missing")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        return requests.post(url, data=data).status_code == 200
    except Exception as e:
        st.warning(f"Telegram error: {e}")
        return False

def safe_fmt(val, digits=2):
    try:
        return f"{val:.{digits}f}"
    except:
        return "N/A"

# Live Time
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"🕒 Last Checked: `{now}`")

# Main Loop
for symbol in symbols:
    st.markdown(f"---\n### 🔍 {symbol}")
    df = fetch_data(symbol)

    if is_data_invalid(df):
        st.warning(f"⚠️ No valid data for {symbol}")
        continue

    df = indicators(df)

    try:
        latest = df["Close"].iloc[-1]
        breakout = df["High"].tail(20).max()
        breakdown = df["Low"].tail(20).min()
        rsi = df["RSI"].iloc[-1]
        macd = df["MACD"].iloc[-1]

        st.markdown(
            f"**Price:** ₹{safe_fmt(latest)} | "
            f"📈 BO: ₹{safe_fmt(breakout)} | "
            f"📉 BD: ₹{safe_fmt(breakdown)} | "
            f"RSI: {safe_fmt(rsi,1)} | "
            f"MACD: {safe_fmt(macd)}"
        )

        alert = None
        if pd.notna(latest) and pd.notna(breakout) and latest > breakout:
            alert = (
                "🚀 *{0} Breakout!*\n"
                "Price: ₹{1} > ₹{2}\n"
                "📊 RSI: {3} | MACD: {4}".format(
                    symbol, safe_fmt(latest), safe_fmt(breakout),
                    safe_fmt(rsi, 1), safe_fmt(macd)
                )
            )
        elif pd.notna(latest) and pd.notna(breakdown) and latest < breakdown:
            alert = (
                "⚠️ *{0} Breakdown!*\n"
                "Price: ₹{1} < ₹{2}\n"
                "📉 RSI: {3} | MACD: {4}".format(
                    symbol, safe_fmt(latest), safe_fmt(breakdown),
                    safe_fmt(rsi, 1), safe_fmt(macd)
                )
            )

        if enable_alerts and alert:
            if send_alert(alert):
                st.success("✅ Alert sent on Telegram")
            else:
                st.warning("⚠️ Failed to send alert")

        if show_chart:
            try:
                plot_chart(df, symbol)
            except Exception as e:
                st.error(f"Chart error: {e}")

    except Exception as e:
        st.error(f"❌ Error processing {symbol}: {e}")
