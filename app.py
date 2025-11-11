# app.py
import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from uszipcode import SearchEngine
import ast

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide")

# ---------------- CSS STYLES ----------------
st.markdown("""
<style>
/* Welcome Screen */
.welcome-screen {
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #fad0c4, #ff9a9e);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    color: white;
    text-align: center;
}
@keyframes gradientBG {
    0%{background-position:0% 50%;}
    50%{background-position:100% 50%;}
    100%{background-position:0% 50%;}
}
.welcome-title {
    font-size: 4rem;
    font-weight: 900;
    text-shadow: 0 0 20px #ff9a9e;
    margin-bottom: 20px;
}
.welcome-subtitle {
    font-size: 1.5rem;
    margin-bottom: 40px;
}
.start-btn {
    font-size: 1.5rem;
    padding: 1rem 3rem;
    border-radius: 30px;
    border: none;
    background: #ff6a00;
    color: white;
    font-weight: bold;
    cursor: pointer;
    animation: pulse 1.5s infinite alternate;
}
@keyframes pulse {
    from {transform: scale(1);}
    to {transform: scale(1.1);}
}
/* Dark theme main page */
.main-page {
    background-color: #121212;
    color: white;
    min-height: 100vh;
    padding: 2rem;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
/* Job cards */
.job-card {
    background-color: #1e1e1e;
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    cursor: pointer;
    transition: background-color 0.3s ease;
}
.job-card:hover {
    background-color: #333;
}
</style>
""", unsafe_allow_html=True)

# ---------------- STATE ----------------
if "started" not in st.session_state:
    st.session_state.started = False

if "jobs_df" not in st.session_state:
    st.session_state.jobs_df = None

# ---------------- WELCOME SCREEN ----------------
if not st.session_state.started:
    st.markdown("""
    <div class="welcome-screen">
        <div class="welcome-title">😊 Keep Smiling Job Finder</div>
        <div class="welcome-subtitle">Find your next opportunity closer to home 💼</div>
        <button class="start-btn">Let's Start</button>
    </div>
    <script>
    const btn = window.parent.document.querySelector('button.start-btn');
    btn.onclick = () => {window.parent.postMessage({func:'startApp'}, '*');}
    </script>
    """, unsafe_allow_html=True)

    if st.button("Let's Start"):
        st.session_state.started = True
        st.experimental_rerun()
    st.stop()

# ---------------- MAIN JOB SEARCH PAGE ----------------
st.markdown('<div class="main-page">', unsafe_allow_html=True)
st.title("😊 Keep Smiling Job Finder")
st.subheader("Upload your job CSV and find nearby opportunities!")

# ---------------- CSV UPLOAD ----------------
uploaded_file = st.file_uploader("📂 Upload Job CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()
    
    # Expand multi-location rows
    rows = []
    for _, r in df.iterrows():
        locs = r.get('location') or r.get('city') or ""
        # Convert stringified lists
        if isinstance(locs, str) and locs.startswith('['):
            try: loc_list = ast.literal_eval(locs)
            except: loc_list = [loc.strip() for loc in locs.split(',')]
        elif isinstance(locs, str) and (',' in locs or ';' in locs):
            sep = ',' if ',' in locs else ';'
            loc_list = [l.strip() for l in locs.split(sep)]
        elif isinstance(locs, list):
            loc_list = locs
        else:
            loc_list = [locs]
        for loc in loc_list:
            new_row = r.copy()
            new_row['city'] = loc
            rows.append(new_row)
    df_expanded = pd.DataFrame(rows)

    # ---------------- CANDIDATE INPUT ----------------
    st.subheader("Enter Your Location")
    col1, col2, col3 = st.columns(3)
    with col1:
        zip_code = st.text_input("ZIP Code (optional)").strip()
    with col2:
        city = st.text_input("City (optional)").strip()
    with col3:
        state = st.text_input("State (optional)").strip()
    radius = st.slider("Search Radius (miles)", 10, 200, 40)
    if st.button("🔍 Find Jobs Nearby"):
        # ---------------- CANDIDATE GEOCODE ----------------
        candidate_loc = None
        search = SearchEngine(simple_zipcode=True)
        if zip_code:
            result = search.by_zipcode(zip_code)
            if result and result.lat and result.lng:
                candidate_loc = (result.lat, result.lng)
        if not candidate_loc and city and state:
            geolocator = Nominatim(user_agent="job_locator_app")
            loc = geolocator.geocode(f"{city}, {state}")
            if loc: candidate_loc = (loc.latitude, loc.longitude)
        if not candidate_loc:
            st.error("❌ Invalid ZIP code or City+State. Please try again.")
            st.stop()
        
        # ---------------- GEOCODE JOB LOCATIONS ----------------
        geolocator = Nominatim(user_agent="job_locator_app")
        lats, lons = [], []
        for idx, row in df_expanded.iterrows():
            try:
                loc_str = f"{row.get('city','')}, {row.get('state','')}"
                loc = geolocator.geocode(loc_str)
                if loc:
                    lats.append(loc.latitude)
                    lons.append(loc.longitude)
                else:
                    lats.append(None)
                    lons.append(None)
            except:
                lats.append(None)
                lons.append(None)
        df_expanded['lat'] = lats
        df_expanded['lon'] = lons
        df_expanded = df_expanded.dropna(subset=['lat','lon'])
        
        # ---------------- CALCULATE DISTANCE ----------------
        df_expanded['distance'] = df_expanded.apply(lambda r: geodesic(candidate_loc,(r['lat'],r['lon'])).miles, axis=1)
        df_near = df_expanded[df_expanded['distance'] <= radius].sort_values('distance')
        
        if df_near.empty:
            st.warning("⚠️ No jobs found within the specified radius.")
        else:
            st.success(f"Found {len(df_near)} job(s) within {radius} miles.")
            # ---------------- SHOW JOB CARDS ----------------
            for idx, row in df_near.iterrows():
                with st.expander(f"{row.get('client','')} - {row.get('job_title','')} - {row.get('city','')} ({row['distance']:.1f} miles)"):
                    st.write(row.to_dict())

st.markdown('</div>', unsafe_allow_html=True)
