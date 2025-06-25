import streamlit as st

def show_navigation():
    return st.selectbox("📂 Choose Section", ["📈 Live Feed", "📉 Analysis", "📥 Feedback"])
