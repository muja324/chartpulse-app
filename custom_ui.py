import streamlit as st

def apply_ui(data=None):
    # --- Custom Styling ---
    st.markdown("""
        <style>
        .stApp { background-color: #0d1117; }
        h1, h2, h3 { color: #facc15; font-family: 'Segoe UI'; }
        .sidebar .sidebar-content { background-color: #1e293b; }
        .signal-box {
            padding: 15px; border-radius: 8px;
            font-size: 18px; font-weight: bold;
            text-align: center; margin-top: 20px;
        }
        .buy { background-color: #166534; color: #f0fdf4; }
        .sell { background-color: #7f1d1d; color: #fee2e2; }
        .hold { background-color: #1e293b; color: #facc15; }
        </style>
    """, unsafe_allow_html=True)

    # --- Header ---
    st.markdown("""
        <div style='background-color:#0d1117;padding:20px;border-radius:10px;margin-bottom:20px;'>
            <h1 style='text-align:center;'>🚀 Mujahidul Finance Hub</h1>
            <p style='text-align:center;color:#cbd5e1;'>Smart. Sharp. Shariah-Compliant.</p>
        </div>
    """, unsafe_allow_html=True)

    # --- Signal Logic (RSI + SMA + Explanation) ---
    if data is not None and not data.empty:
        try:
            # Indicator calculation
            data['SMA20'] = data['Close'].rolling(window=20).mean()

            delta = data['Close'].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            data['RSI'] = 100 - (100 / (1 + rs))

            rsi = data['RSI'].iloc[-1]
            close = data['Close'].iloc[-1]
            sma = data['SMA20'].iloc[-1]

            # Signal
            if rsi < 30 and close > sma:
                signal = "🟢 BUY - RSI oversold and price above SMA"
                css_class = "buy"
                explanation = "RSI is below 30 (oversold) and price is trading above SMA — this often indicates a recovery bounce, signaling a potential entry point."
            elif rsi > 70 and close < sma:
                signal = "🔴 SELL - RSI overbought and below SMA"
                css_class = "sell"
                explanation = "RSI is above 70 (overbought) and price is under SMA — this suggests weakness after a rally, possibly signaling a pullback or reversal."
            else:
                signal = "🟡 HOLD - No strong signal"
                css_class = "hold"
                explanation = "The indicators are neutral — RSI is in mid-range and price is close to or within the SMA band."

            # Signal Box
            st.markdown(f"<div class='signal-box {css_class}'>{signal}</div>", unsafe_allow_html=True)

            # Explanation Box
            st.markdown(f"""
                <div style='background-color:#0f172a;padding:15px;border-radius:8px;margin-top:10px;color:#cbd5e1;font-size:15px;'>
                    <b>🧠 Why this signal?</b><br>
                    {explanation}
                </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.warning(f"Signal calculation error: {e}")

    # --- Footer ---
    st.markdown("""
        <hr style='margin-top:50px;'>
        <div style='text-align:center;color:#94a3b8;font-size:12px;'>
            Made with 💼 by <b>Mujahidul</b> | Inspired by Wisdom, Powered by Data
        </div>
    """, unsafe_allow_html=True)
