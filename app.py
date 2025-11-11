# app.py
import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide")

# ---------------- ANIMATED WELCOME SCREEN ----------------
st.markdown("""
<style>
body {
  margin: 0;
  padding: 0;
  background: linear-gradient(135deg, #141E30, #243B55);
  background-size: 400% 400%;
  animation: bgmove 10s infinite alternate;
  overflow: hidden;
}
@keyframes bgmove {
  0% {background-position: left;}
  100% {background-position: right;}
}
.center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: white;
}
.title {
  font-size: 72px;
  font-weight: 900;
  background: linear-gradient(to right, #00f2fe, #4facfe);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: fadeIn 2s ease-in-out;
}
.subtitle {
  font-size: 28px;
  color: #cce7ff;
  margin-top: 10px;
  opacity: 0.9;
  animation: fadeIn 3s ease-in-out;
}
@keyframes fadeIn {
  from {opacity: 0; transform: scale(0.95);}
  to {opacity: 1; transform: scale(1);}
}
.button {
  margin-top: 40px;
  background-color: #00c6ff;
  border: none;
  border-radius: 25px;
  color: white;
  padding: 15px 40px;
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
  transition: 0.3s;
  animation: fadeIn 3.5s ease-in-out;
}
.button:hover {
  transform: scale(1.1);
  box-shadow: 0 0 20px #00f2fe;
}
</style>
""", unsafe_allow_html=True)

if "show_main" not in st.session_state:
    st.session_state.show_main = False

if not st.session_state.show_main:
    st.markdown("""
    <div class="center">
      <h1 class="title">😊 Keep Smiling Job Finder</h1>
      <h3 class="subtitle">Find your next opportunity within miles 💼</h3>
      <form action="#" method="get">
        <button class="button" id="start-btn">Let's Start 🚀</button>
      </form>
    </div>
    """, unsafe_allow_html=True)
    btn = st.button("Let's Start 🚀", use_container_width=True)
    time.sleep(2)
    st.session_state.show_main = True
    st.rerun()

# ---------------- MAIN INTERFACE ----------------
st.title("🌍 Keep Smiling Job Finder")
st.markdown("Upload your job list, enter candidate location, and explore nearby openings instantly!")

uploaded = st.file_uploader("📂 Upload Job CSV (columns: Client, Job_Title, City, State, etc.)", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    df.columns = df.columns.str.strip().str.lower()
    st.success(f"✅ Loaded {len(df)} jobs successfully!")

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

    @st.cache_data(show_spinner=False)
    def geo(place):
        try:
            loc = geolocator.geocode(f"{place}, USA", timeout=10)
            if loc:
                return loc.latitude, loc.longitude
        except:
            return None, None
        return None, None

    if find:
        with st.spinner("📍 Locating jobs near you..."):
            cand = None
            if zip_code:
                cand = geo(str(zip_code))
            if (not cand) or (None in cand):
                if city and state:
                    cand = geo(f"{city}, {state}")
            if (not cand) or (None in cand):
                st.error("❌ Could not find location. Please check ZIP/City/State.")
                st.stop()

            df["full_location"] = df.apply(lambda r: f"{r.get('city','')}, {r.get('state','')}", axis=1)
            unique_places = df["full_location"].unique()
            locmap = {x: geo(x) for x in unique_places}
            df[["lat", "lon"]] = df["full_location"].apply(lambda x: pd.Series(locmap[x]))
            df = df.dropna(subset=["lat", "lon"])
            df["distance"] = df.apply(lambda r: geodesic(cand, (r["lat"], r["lon"])).miles, axis=1)
            df_near = df[df["distance"] <= radius].sort_values("distance")

            if df_near.empty:
                st.warning("⚠️ No jobs found within this range.")
            else:
                st.markdown(f"## ✨ {len(df_near)} Jobs Available Within {radius} Miles")

                for i, r in df_near.iterrows():
                    st.markdown(f"""
                    <div style="background:#001F3F; border-radius:15px; padding:20px; margin-bottom:15px; color:white;">
                        <h3>💼 {r.get('job_title','')} at {r.get('client','')}</h3>
                        <p><b>📍 Location:</b> {r.get('city','')} | <b>Distance:</b> {r['distance']:.1f} miles</p>
                        <details style="margin-top:10px;">
                            <summary style="cursor:pointer; color:#00e6ff;"><b>View Details</b></summary>
                            <div style="margin-top:10px;">
                                {''.join([f"<p><b>{c.capitalize()}:</b> {r[c]}</p>" for c in df.columns if c not in ['lat','lon','distance','full_location']])}
                            </div>
                        </details>
                    </div>
                    """, unsafe_allow_html=True)
else:
    st.info("📥 Please upload a CSV file to begin searching.")
