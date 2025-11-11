# app.py
import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time, ast

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide")

# ---------------- WELCOME ANIMATION ----------------
st.markdown("""
<style>
body {
  margin:0; padding:0;
  background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
  background-size: 400% 400%;
  animation: bgmove 8s ease infinite;
}
@keyframes bgmove {
  0% {background-position: 0% 50%;}
  50% {background-position: 100% 50%;}
  100% {background-position: 0% 50%;}
}
.center-screen {
  height: 100vh;
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  text-align: center;
}
.title {
  font-size: 70px; font-weight: 900;
  background: linear-gradient(90deg,#00f2fe,#4facfe);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px #00f2fe,0 0 40px #4facfe;
  animation: fadeIn 2s ease-in-out forwards;
}
.subtitle {
  font-size: 28px; color: #cce7ff; margin-top: 10px;
  opacity:0; animation: fadeInSub 2.5s forwards;
}
@keyframes fadeIn {from{opacity:0; transform:scale(0.95);} to{opacity:1; transform:scale(1);}}
@keyframes fadeInSub {from{opacity:0;} to{opacity:0.9;}}
.start-btn {
  margin-top: 40px; padding: 15px 50px; font-size:24px;
  font-weight:bold; border-radius:30px; border:none;
  background:#00c6ff; color:white; cursor:pointer;
  animation:pulse 1.5s infinite alternate;
}
@keyframes pulse {from{transform:scale(1);} to{transform:scale(1.1);}}
</style>
""", unsafe_allow_html=True)

if "show_main" not in st.session_state:
    st.session_state.show_main = False

# Welcome page
if not st.session_state.show_main:
    st.markdown("""
    <div class="center-screen">
        <h1 class="title">😊 Keep Smiling Job Finder</h1>
        <h3 class="subtitle">Find your next opportunity closer to home 💼</h3>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Let's Start"):
        st.session_state.show_main = True
        st.experimental_rerun()

# ---------------- MAIN JOB FINDER ----------------
if st.session_state.show_main:
    st.title("🌍 Keep Smiling Job Finder")
    st.markdown("Upload your job CSV and find jobs nearby!")

    uploaded = st.file_uploader("📂 Upload Job CSV (columns: Client, Job_Title, Location, City, State, etc.)", type=["csv"])

    if uploaded:
        df = pd.read_csv(uploaded)
        df.columns = df.columns.str.strip().str.lower()
        st.success(f"✅ Loaded {len(df)} jobs successfully!")

        # ---------------- MULTI-LOCATION EXPANSION ----------------
        rows = []
        for _, r in df.iterrows():
            locs = r["location"]
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

        # ---------------- SEARCH INPUT ----------------
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

        # ---------------- SEARCH & FILTER ----------------
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

                df_expanded["full_location"] = df_expanded.apply(lambda r: f"{r.get('location','')}, {r.get('state','')}", axis=1)
                unique_places = df_expanded["full_location"].unique()
                locmap = {x: geo(x) for x in unique_places}
                df_expanded[["lat","lon"]] = df_expanded["full_location"].apply(lambda x: pd.Series(locmap[x]))
                df_expanded = df_expanded.dropna(subset=["lat","lon"])
                df_expanded["distance"] = df_expanded.apply(lambda r: geodesic(cand, (r["lat"], r["lon"])).miles, axis=1)
                df_near = df_expanded[df_expanded["distance"] <= radius].sort_values("distance")

                if df_near.empty:
                    st.warning("⚠️ No jobs found within this range.")
                else:
                    st.markdown(f"## ✨ {len(df_near)} Jobs Available Within {radius} Miles")
                    for _, r in df_near.iterrows():
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
