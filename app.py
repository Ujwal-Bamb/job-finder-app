# app.py
import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide")

# ---------------- ANIMATED INTRO ----------------
st.markdown("""
<style>
body {
  background: linear-gradient(-45deg,#ff9a9e,#fad0c4,#a1c4fd,#c2e9fb);
  background-size:400% 400%;
  animation:grad 8s ease infinite;
}
@keyframes grad {
  0%{background-position:0% 50%;}
  50%{background-position:100% 50%;}
  100%{background-position:0% 50%;}
}
.welcome{margin-top:35vh;text-align:center;color:white;}
.welcome h1{
  font-size:60px;font-weight:900;text-shadow:0 0 20px #fff;
  animation:bounce 1.5s infinite alternate;
}
@keyframes bounce{0%{transform:translateY(0);}100%{transform:translateY(-15px);}}
.sub{font-size:24px;opacity:.9;animation:fadeIn 2s;}
@keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
</style>
""", unsafe_allow_html=True)

if "main" not in st.session_state:
    st.session_state.main = False
if not st.session_state.main:
    st.markdown("<div class='welcome'><h1>😊 Keep Smiling Job Finder</h1><div class='sub'>Helping you find your next opportunity closer to home 💼</div></div>", unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.main = True
    st.rerun()

# ---------------- MAIN UI ----------------
st.title("🌍 Find Nearby Jobs")
st.markdown("Upload your job list, enter candidate location, and explore nearby openings instantly!")

uploaded = st.file_uploader("📂 Upload Job CSV (columns: Client, Job_Title, City, State, etc.)", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
    df.columns = df.columns.str.strip().str.lower()
    st.success(f"✅ Loaded {len(df)} jobs")

    col1, col2, col3 = st.columns(3)
    with col1: zip_code = st.text_input("📮 ZIP Code (optional)")
    with col2: city = st.text_input("🏙️ City (optional)")
    with col3: state = st.text_input("🗺️ State (optional)")
    radius = st.slider("🎯 Search Radius (mi)", 10, 200, 40)
    find = st.button("🔍 Find Jobs", use_container_width=True)

    geolocator = Nominatim(user_agent="job_locator")

    @st.cache_data(show_spinner=False)
    def geo(place):
        try:
            loc = geolocator.geocode(f"{place}, USA", timeout=10)
            if loc: return loc.latitude, loc.longitude
        except: return None, None
        return None, None

    if find:
        with st.spinner("Locating jobs near you…"):
            cand = None
            if zip_code:
                cand = geo(str(zip_code))
            if (not cand) or (None in cand):
                if city and state:
                    cand = geo(f"{city}, {state}")
            if (not cand) or (None in cand):
                st.error("❌ Could not find location. Check ZIP/City/State.")
                st.stop()

            df["full_location"] = df.apply(lambda r: f"{r.get('city','')}, {r.get('state','')}", axis=1)
            u = df["full_location"].unique()
            locmap = {x: geo(x) for x in u}
            df[["lat","lon"]] = df["full_location"].apply(lambda x: pd.Series(locmap[x]))
            df = df.dropna(subset=["lat","lon"])
            df["distance"] = df.apply(lambda r: geodesic(cand,(r["lat"],r["lon"])).miles, axis=1)
            df_near = df[df["distance"] <= radius].sort_values("distance")

            if df_near.empty:
                st.warning("⚠️ No jobs found within this range.")
            else:
                st.markdown(f"### 🎯 {len(df_near)} Jobs Available Within {radius} Miles")

                for i, r in df_near.iterrows():
                    with st.expander(f"💼 {r.get('job_title','')} — {r.get('client','')} ({r.get('city','')}) — {r['distance']:.1f} mi"):
                        for c in df.columns:
                            st.write(f"**{c.capitalize()}**: {r[c]}")
