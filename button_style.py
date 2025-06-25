import streamlit as st

def show_cta_button(label="🔍 Analyze", key="analyze"):
    st.markdown("""
        <style>
        .glow-button {
            background-color: #facc15;
            color: black;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 8px;
            font-weight: bold;
            border: none;
            transition: all 0.2s ease-in-out;
        }
        .glow-button:hover {
            box-shadow: 0 0 12px #facc15;
            transform: scale(1.05);
        }
        </style>
    """, unsafe_allow_html=True)

    return st.button(f"<span class='glow-button'>{label}</span>", key=key, help="Click to update", unsafe_allow_html=True)
