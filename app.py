import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import ta  # Technical Analysis library
from loader import show_loader
from responsive_tabs import show_navigation
from custom_ui import apply_ui

# --- Page Setup ---
st.set_page_config(page_title="ChartPulse", layout="wide")
st.title("📈 ChartPulse — Live Stock Signal Tracker")

# --- Sidebar Settings ---
st.sidebar.header("⚙️ Settings")
symbols = st.sidebar.text_area("Stock Symbols (comma-separated)", "RELIANCE.NS, TCS.NS").split(",")
symbols = [s.strip().upper() for s in symbols if s.strip()]
show_chart = st.sidebar.checkbox("📊 Show Chart", True)
enable_alerts = st.sidebar.checkbox("📲 Telegram Alerts", False)

# --- Interval Selector ---
interval = st.selectbox("🕒 Select Interval", ["15m", "30m", "1h", "1d"], index=3)
period = "6mo" if interval == "1d" else "5d"

# --- Auto Refresh ---
REFRESH_INTERVAL = 1  # in minutes
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

        # Add technical indicators
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14, fillna=True)
        macd = ta.trend.MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9, fillna=True)
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()

        return df
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def is_data_invalid(df):
    if not isinstance(df, pd.DataFrame) or df.empty:
        return True
    if any(col not in df.columns for col in ["Open", "High", "Low", "Close"]):
        return True
    if df["Close"].dropna().shape[0] < 5:
        return True
    return False

def plot_chart(df, symbol):
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
        row_heights=[0.4, 0.15, 0.2, 0.25],
        subplot_titles=(f"{symbol} — Candlestick", "Volume", "RSI (14)", "MACD")
    )

    # --- Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Candles",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350"
    ), row=1, col=1)

    # --- Volume
    fig.add_trace(go.Bar(
        x=df.index,
        y=df["Volume"],
        name="Volume",
        marker_color="#90caf9"
    ), row=2, col=1)

    # --- RSI
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["RSI"],
        name="RSI",
        line=dict(color="#2962FF", width=2)
    ), row=3, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)

    # --- MACD
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["MACD"],
        name="MACD",
        line=dict(color="blue", width=2)
    ), row=4, col=1)
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["MACD_signal"],
        name="MACD Signal",
        line=dict(color="orange", width=2)
    ), row=4, col=1)

    # --- Support/Resistance (last 20 candles)
    resistance = df["High"].tail(20).max()
    support = df["Low"].tail(20).min()
    fig.add_hline(y=resistance, line_color="red", line_dash="dash", annotation_text="Resistance", row=1, col=1)
    fig.add_hline(y=support, line_color="green", line_dash="dash", annotation_text="Support", row=1, col=1)

    # --- Trendline (simple: last 10 close points)
    trend_df = df["Close"].tail(10)
    fig.add_trace(go.Scatter(
        x=trend_df.index,
        y=trend_df.values,
        mode="lines",
        name="Trendline",
        line=dict(color="purple", width=2, dash="dot")
    ), row=1, col=1)

    # --- Layout Settings
    fig.update_layout(
        height=1000,
        showlegend=False,
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        dragmode="pan",
        hovermode="x unified",
        xaxis=dict(fixedrange=False),
        yaxis=dict(fixedrange=False),
        yaxis2=dict(fixedrange=False),
        yaxis3=dict(fixedrange=False),
        yaxis4=dict(fixedrange=False),
        xaxis4_rangeslider_visible=False
    )

    # --- Scroll Zoom On
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

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
