import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# ---------- Streamlit Setup ----------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide", page_icon="😊")

# ---------- Custom CSS ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #e0f2ff, #ffffff);
    font-family: 'Segoe UI', sans-serif;
}

h1, h2, h3 {
    color: #1e3a8a;
    font-weight: 700;
    text-align: center;
}

#welcome-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    text-align: center;
}

#welcome-container img {
    border-radius: 12px;
    margin: 25px 0;
}

.start-btn {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 10px;
    padding: 14px 34px;
    font-size: 22px;
    font-weight: 600;
    transition: all 0.3s ease-in-out;
    box-shadow: 0 4px 10px rgba(37,99,235,0.3);
    cursor: pointer;
}
.start-btn:hover {
    background: linear-gradient(135deg, #1d4ed8, #2563eb);
    transform: scale(1.08);
}
</style>
""", unsafe_allow_html=True)

# ---------- State ----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ---------- Welcome Page ----------
if st.session_state.page == "welcome":
    st.markdown("""
    <div id="welcome-container">
        <h1>😊 Keep Smiling Job Finder</h1>
        <h3>💼 Find your next job closer to home</h3>
        <img src="https://media.giphy.com/media/xT1R9I7Ne3mAQhXcWc/giphy.gif" width="260">
        <p style="font-size:18px; color:#1e293b;">Upload your job list and discover nearby opportunities instantly!</p>
    </div>
    """, unsafe_allow_html=True)

    # Streamlit button for interactivity
    if st.button("🚀 Let's Start", key="start"):
        st.session_state.page = "main"
        st.experimental_rerun()

# ---------- Main Page ----------
elif st.session_state.page == "main":
    st.title("📝 Job Finder Dashboard")
    st.write("Upload your CSV and discover nearby opportunities!")
