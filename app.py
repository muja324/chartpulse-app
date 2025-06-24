import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# Load Secrets
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
REFRESH_INTERVAL = int(st.secrets.get("REFRESH_INTERVAL", 5))

# Auto-refresh every REFRESH_INTERVAL mins
st_autorefresh(interval=REFRESH_INTERVAL * 60 * 1000, key="datarefresh")

# UI setup
st.set_page_config(page_title="ChartPulse", layout="wide")
st.title("📈 ChartPulse — Live Stock Signal Tracker")
st.sidebar.header("⚙️ Settings")

symbols = st.sidebar.text_area("Enter Stock Symbols (comma-separated)", "RELIANCE.NS, ASTERDM.NS").split(",")
symbols = [s.strip().upper() for s in symbols if s.strip()]
show_chart = st.sidebar.checkbox("📊 Show Candlestick Chart", True)
enable_alerts = st.sidebar.checkbox("📲 Send Telegram Alerts", True)

def fetch_data(symbol):
    try:
        return yf.download(symbol, period="5d", interval="15m")
    except:
        return pd.DataFrame()

def indicators(df):
    df["RSI"] = df["Close"].rolling(14).apply(
        lambda x: 100 - (100 / (1 + (x.diff().clip(lower=0).sum() / x.diff().clip(upper=0).abs().sum())))
    )
    exp1 = df["Close"].ewm(span=12).mean()
    exp2 = df["Close"].ewm(span=26).mean()
    df["MACD"] = exp1 - exp2
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    return df

def plot_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df["Open"],
        high=df["High"], low=df["Low"], close=df["Close"]
    )])
    fig.update_layout(title=f"{symbol} - 15 Min Chart", height=400)
    st.plotly_chart(fig, use_container_width=True)

def send_alert(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        return requests.post(url, data=data).status_code == 200
    except Exception as e:
        st.warning(f"Telegram alert failed: {e}")
        return False

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"🕒 Last checked: `{now}`")

for symbol in symbols:
    st.markdown(f"---\n### 🔎 {symbol}")
    df = fetch_data(symbol)
    if df.empty or "Close" not in df.columns:
        st.error(f"No data for {symbol}")
        continue

    df = indicators(df)
    latest = df["Close"].iloc[-1]
    breakout = df["High"].tail(20).max()
    breakdown = df["Low"].tail(20).min()
    rsi = df["RSI"].iloc[-1]
    macd = df["MACD"].iloc[-1]

    st.markdown(f"**Price:** ₹{latest:.2f} | 📈 BO: ₹{breakout:.2f} | 📉 BD: ₹{breakdown:.2f} | RSI: {rsi:.1f} | MACD: {macd:.2f}")

    if latest > breakout:
        alert = f"🚀 *{symbol} Breakout!* ₹{latest:.2f} > ₹{breakout:.2f}\n📊 RSI: {rsi:.1f} | MACD: {macd:.2f}"
    elif latest < breakdown:
        alert = f"⚠️ *{symbol} Breakdown!* ₹{latest:.2f} < ₹{breakdown:.2f}\n📉 RSI: {rsi:.1f} | MACD: {macd:.2f}"
    else:
        alert = None

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
