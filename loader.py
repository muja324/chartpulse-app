import streamlit as st
import time

def show_loader(text="⏳ Fetching market intelligence..."):
    with st.spinner(text):
        time.sleep(1.5)
