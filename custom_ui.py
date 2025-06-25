import streamlit as st

def apply_ui():
    # --- Custom Page Styling ---
    st.markdown("""
        <style>
        body {
            background-color: #0d1117;
            color: #f1f5f9;
        }
        .stApp {
            background-color: #0d1117;
        }
        h1, h2, h3, h4 {
            color: #facc15;
        }
        .sidebar .sidebar-content {
            background-color: #1e293b;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Branded Header ---
    st.markdown("""
        <div style='background-color:#0d1117;padding:20px;border-radius:10px;margin-bottom:20px;'>
            <h1 style='text-align:center;color:#facc15;'>🚀 Mujahidul Finance Hub</h1>
            <p style='text-align:center;color:#cbd5e1;'>Smart. Sharp. Shariah-Compliant.</p>
        </div>
    """, unsafe_allow_html=True)

    # --- Footer Branding ---
    st.markdown("""
        <hr style='margin-top:50px;'>
        <div style='text-align:center;color:#94a3b8;font-size:12px;'>
            Made with 💼 by <b>Mujahidul</b> | Inspired by Wisdom, Powered by Data
        </div>
    """, unsafe_allow_html=True)
