import streamlit as st

def apply_ui(df):
    # --- Universal Style ---
    st.markdown("""
        <style>
        .main {
            background-color: #f8f9fa;
        }
        .title-text {
            font-size: 28px;
            font-weight: 700;
            color: #0a3d62;
        }
        .signal-box {
            border: 2px solid #ced6e0;
            padding: 1rem;
            border-radius: 10px;
            background-color: #ffffff;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        }
        .tag {
            padding: 4px 10px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 13px;
            color: white;
        }
        .tag-green { background-color: #10ac84; }
        .tag-red { background-color: #ee5253; }
        .tag-gray { background-color: #8395a7; }
        </style>
    """, unsafe_allow_html=True)

    # --- Branding Header (Always visible) ---
    st.markdown('<div class="title-text">📊 ChartPulse — Signal Overview</div>', unsafe_allow_html=True)
    st.markdown("")

    # --- Signal Block ---
    st.markdown('<div class="signal-box">', unsafe_allow_html=True)

    if df is None or df.empty or "Close" not in df.columns:
        st.markdown(
            '<span class="tag tag-gray">No valid data available for this stock.</span>',
            unsafe_allow_html=True
        )
    else:
        try:
            close = df["Close"].iloc[-1]
            high = df["High"].tail(20).max()
            low = df["Low"].tail(20).min()

            if close > high:
                st.markdown(
                    f'<span class="tag tag-green">🚀 Breakout Detected! ₹{close:.2f}</span>',
                    unsafe_allow_html=True
                )
            elif close < low:
                st.markdown(
                    f'<span class="tag tag-red">⚠️ Breakdown Detected! ₹{close:.2f}</span>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<span class="tag tag-gray">No active signal. Last Price: ₹{close:.2f}</span>',
                    unsafe_allow_html=True
                )
        except Exception:
            st.markdown(
                '<span class="tag tag-gray">Signal data unavailable.</span>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)
