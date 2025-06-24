import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import time
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# --- Load secrets ---
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")
REFRESH_INTERVAL = int(st.secrets.get("REFRESH_INTERVAL", 5))

# --- App UI ---
st.set_page_config(page_title="ChartPulse: Live Breakout App", layout="wide")
st.title("📊 ChartPulse — Live Stock Signal Tracker")
st.sidebar.header("⚙️ Settings")

symbols = st.sidebar.text_area("Enter stock symbols (comma-separated)", "ASTERDM.NS, RELIANCE.NS").split(",")
symbols = [s.strip().upper() for s in symbols if s.strip()]
show_chart = st.sidebar.checkbox("📈 Show Live Chart", True)
enable_alerts = st.sidebar.checkbox("📲 Enable Telegram Alerts", True)

placeholder = st.empty()
log_holder = st.container()

# --- Helper functions ---
def fetch_data(symbol):
    return yf.download(symbol, period="5d", interval="15m")

def calculate_indicators(df):
    df["RSI"] = df["Close"].rolling(14).apply(lambda x: 100 - (100 / (1 + (x.diff().clip(lower=0).sum() / x.diff().clip(upper=0).abs().sum()))))
    exp1 = df["Close"].ewm(span=12).mean()
    exp2 = df["Close"].ewm(span=26).mean()
    df["MACD"] = exp1 - exp2
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    return df

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg}
        response = requests.post(url, data=payload)
        return response.status_code == 200
    except:
        return False

def plot_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"]
    )])
    fig.update_layout(title=f"{symbol} - 15min", height=400)
    st.plotly_chart(fig, use_container_width=True)

# --- Main app loop ---
while True:
    with placeholder.container():
        now = datetime.now().strftime("%H:%M:%S")
        st.subheader(f"🕒 Last Refreshed: {now}")

        for symbol in symbols:
            df = fetch_data(symbol)
            if df.empty or "Close" not in df.columns:
                st.warning(f"{symbol} data not available.")
                continue

            df = calculate_indicators(df)
            breakout = df["High"].tail(20).max()
            breakdown = df["Low"].tail(20).min()
            latest = df["Close"].iloc[-1]
            rsi = df["RSI"].iloc[-1]
            macd = df["MACD"].iloc[-1]
            signal = df["Signal"].iloc[-1]

            st.markdown(f"**{symbol}** → ₹{latest:.2f} | BO: ₹{breakout:.2f} | BD: ₹{breakdown:.2f} | RSI: {rsi:.1f} | MACD: {macd:.2f}")

            alert_msg = None
            if latest > breakout:
                alert_msg = f"🚀 *{symbol} Breakout!* ₹{latest:.2f} > ₹{breakout:.2f}"
            elif latest < breakdown:
                alert_msg = f"⚠️ *{symbol} Breakdown!* ₹{latest:.2f} < ₹{breakdown:.2f}"

            if enable_alerts and alert_msg:
                alert_msg += f"\n📊 RSI: {rsi:.1f} | MACD: {macd:.2f}"
                sent = send_alert(alert_msg)
                if sent:
                    st.success(f"Alert sent for {symbol}")
                else:
                    st.error("⚠️ Failed to send alert.")

            if show_chart:
                plot_chart(df, symbol)

    time.sleep(REFRESH_INTERVAL * 60)
    st.rerun()
