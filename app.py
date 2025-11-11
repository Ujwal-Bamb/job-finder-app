# app.py
import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import ast

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide")

# ---------------- WELCOME SCREEN ----------------
st.markdown("""
<style>
body {
  margin:0;
  padding:0;
}
.welcome-page {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg,#ff7eb3,#ff758c,#ff7e5f,#feb47b);
  background-size: 400% 400%;
  animation: gradientBG 8s ease infinite;
  flex-direction: column;
  text-align: center;
}
@keyframes gradientBG {
  0% {background-position:0% 50%;}
  50% {background-position:100% 50%;}
  100% {background-position:0% 50%;}
}
.title {
  font-size: 64px;
  font-weight: 900;
  background: linear-gradient(to right, #fff200, #ff6a00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px #fffa65, 0 0 40px #ff6a00;
  animation: fadeIn 2s ease-in-out forwards;
}
.subtitle {
  font-size: 28px;
  color: #fff8e1;
  margin-top: 10px;
  opacity: 0;
  animation: fadeInSub 2s forwards;
}
@keyframes fadeIn {
  from {opacity:0; transform: scale(0.95);}
  to {opacity:1; transform: scale(1);}
}
@keyframes fadeInSub {
  from {opacity:0;}
  to {opacity:0.9;}
}
.start-btn {
  margin-top: 40px;
  padding: 15px 50px;
  font-size: 24px;
  font-weight: bold;
  border-radius: 30px;
  border: none;
  background: #ff6a00;
  color: white;
  cursor: pointer;
  animation: pulse 1.5s infinite alternate;
}
@keyframes pulse {
  from {transform: scale(1);}
  to {transform: scale(1.1);}
}
</style>
""", unsafe_allow_html=True)

if "main_page" not in st.session_state:
    st.session_state.main_page = False

if not st.session_state.main_page:
    st.markdown("""
    <div class="welcome-page">
        <h1 class="title">😊 Keep Smiling Job Finder</h1>
        <h3 class="subtitle">Find your next opportunity closer to home 💼</h3>
    </div>
    """, unsafe_allow_html=True)
    start = st.button("🚀 Let's Start")
    if start:
        st.session_state.main_page = True
        st.experimental_rerun()
    st.stop()

# ---------------- MAIN JOB SEARCH ----------------
st.title("🌍 Keep Smiling Job Finder")
st.markdown("Upload your job CSV, enter candidate location, and explore nearby openings instantly!")

# ---------------- FILE UPLOAD ----------------
uploaded = st.file_uploader("📂 Upload Job CSV (columns: Client, Job_Title, City, State, Location, Positions, etc.)", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    df.columns = df.columns.str.strip().str.lower()
    st.success(f"✅ Loaded {len(df)} jobs successfully!")

    # ---------------- CANDIDATE INPUT ----------------
    col1, col2, col3 = st.columns(3)
    with col1:
        zip_code = st.text_input("📮 ZIP Code (optional)")
    with col2:
        city = st.text_input("🏙️ City (optional)")
    with col3:
        state = st.text_input("🗺️ State (optional)")

    radius = st.slider("🎯 Search Radius (miles)", 10, 200, 40)
    find = st.button("🔍 Find Jobs Near Me", use_container_width=True)

    geolocator = Nominatim(user_agent="job_locator")

    # ---------------- HELPER FUNCTION ----------------
    @st.cache_data(show_spinner=False)
    def geo(place):
        try:
            loc = geolocator.geocode(f"{place}, USA", timeout=10)
            if loc:
                return loc.latitude, loc.longitude
        except:
            return None, None
        return None, None

    # ---------------- EXPAND MULTIPLE LOCATIONS ----------------
    if find:
        with st.spinner("📍 Locating jobs near you..."):
            # Candidate location
            cand = None
            if zip_code:
                cand = geo(str(zip_code))
            if (not cand) or (None in cand):
                if city and state:
                    cand = geo(f"{city}, {state}")
            if (not cand) or (None in cand):
                st.error("❌ Could not find location. Please check ZIP/City/State.")
                st.stop()

            # Expand multiple locations per job
            rows = []
            for _, r in df.iterrows():
                locs = r.get("location", "")
                if isinstance(locs, str) and locs.startswith('['):
                    try:
                        loc_list = ast.literal_eval(locs)
                    except:
                        loc_list = [loc.strip() for loc in locs.split(',')]
                elif isinstance(locs, list):
                    loc_list = locs
                else:
                    loc_list = [locs]
                for loc in loc_list:
                    new_row = r.copy()
                    new_row["location"] = loc.strip()
                    rows.append(new_row)
            df_expanded = pd.DataFrame(rows)

            # Geocode job locations
            df_expanded["full_location"] = df_expanded.apply(lambda r: f"{r.get('location','')}, {r.get('state','')}", axis=1)
            unique_places = df_expanded["full_location"].unique()
            locmap = {x: geo(x) for x in unique_places}
            df_expanded[["lat", "lon"]] = df_expanded["full_location"].apply(lambda x: pd.Series(locmap[x]))
            df_expanded = df_expanded.dropna(subset=["lat","lon"])

            # Calculate distance
            df_expanded["distance"] = df_expanded.apply(lambda r: geodesic(cand, (r["lat"], r["lon"])).miles, axis=1)
            df_near = df_expanded[df_expanded["distance"] <= radius].sort_values("distance")

            if df_near.empty:
                st.warning("⚠️ No jobs found within this range.")
            else:
                st.markdown(f"## ✨ {len(df_near)} Jobs Available Within {radius} Miles")
                for i, r in df_near.iterrows():
                    st.markdown(f"""
                    <div style="background:#001F3F; border-radius:15px; padding:20px; margin-bottom:15px; color:white;">
                        <h3>💼 {r.get('job_title','')} at {r.get('client','')}</h3>
                        <p><b>📍 Location:</b> {r.get('location','')} | <b>Distance:</b> {r['distance']:.1f} miles</p>
                        <details style="margin-top:10px;">
                            <summary style="cursor:pointer; color:#00e6ff;"><b>View Details</b></summary>
                            <div style="margin-top:10px;">
                                {''.join([f"<p><b>{c.capitalize()}:</b> {r[c]}</p>" for c in df_expanded.columns if c not in ['lat','lon','distance','full_location']])}
                            </div>
                        </details>
                    </div>
                    """, unsafe_allow_html=True)
else:
    st.info("📥 Please upload a CSV file to begin searching.")
