import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches
import traceback

# ----------- Streamlit Setup -----------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide", page_icon="😊")

# ----------- CSS (unchanged) -----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #e0f2ff, #f5f7ff);
    font-family: 'Segoe UI', sans-serif;
}
.job-card { background: white; border-radius: 12px; padding: 18px; margin: 10px 0; box-shadow: 0 4px 10px rgba(37,99,235,0.1); }
.job-card h4 { color: #1e3a8a; margin-bottom: 8px; }
.job-card p { margin: 4px 0; font-size: 15px; }
</style>
""", unsafe_allow_html=True)

# ----------- Session state ----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ----------- Welcome ----------
if st.session_state.page == "welcome":
    st.markdown("""
    <div style="text-align:center">
        <h1>😊 Keep Smiling Job Finder</h1>
        <h3>💼 Find your next job closer to home</h3>
        <p style="font-size:18px; color:#1e293b;">Upload your job list and discover nearby opportunities instantly!</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Let's Start", key="start-main"):
            st.session_state.page = "main"
            st.rerun()

# ----------- Main ----------
elif st.session_state.page == "main":
    st.title("😊 Keep Smiling Job Finder")
    st.write("Search caregiver job listings by city or ZIP code in California.")

    # ---- Load CA city/ZIP data (with debug) ----
    @st.cache_data(ttl=3600)
    def load_ca_data():
        url = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/california_cities_minimal.csv"
        df = pd.read_csv(url)
        cities, zips = {}, {}
        for _, row in df.iterrows():
            cities[str(row['city']).strip().lower()] = (row['lat'], row['lng'])
            if pd.notna(row.get('zips', None)):
                for z in str(row['zips']).split():
                    zips[z.strip()] = (row['lat'], row['lng'])
        return cities, zips

    # attempt to load and show friendly error if it fails
    try:
        CA_CITIES, ZIP_COORDS = load_ca_data()
        st.info(f"Loaded {len(CA_CITIES)} CA cities and {len(ZIP_COORDS)} ZIP coords.")
    except Exception as e:
        st.error("Failed to load CA city data from GitHub. See details below.")
        st.text(traceback.format_exc())
        st.stop()

    # ---- helper functions ----
    def get_coords(name):
        if not name:
            return None
        name = str(name).strip().lower().split(",")[0]
        if name in CA_CITIES:
            return CA_CITIES[name]
        match = get_close_matches(name, CA_CITIES.keys(), n=1, cutoff=0.75)
        return CA_CITIES[match[0]] if match else None

    def haversine(c1, c2):
        if not c1 or not c2:
            return float('inf')
        R = 3958.8  # miles
        lat1, lon1 = map(radians, c1)
        lat2, lon2 = map(radians, c2)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    # ---- Upload CSV ----
    st.markdown("### 📂 Upload Job List")
    file = st.file_uploader("Upload your CSV (columns: client_name, location, language, pay_rate, schedule)", type=["csv"])

    if not file:
        st.info("Please upload a CSV to continue.")
        st.stop()

    # read CSV with try/except and show details on error
    try:
        jobs = pd.read_csv(file)
    except Exception as e:
        st.error("Error reading the uploaded CSV. See traceback below.")
        st.text(traceback.format_exc())
        st.stop()

    # normalize columns
    try:
        jobs.columns = jobs.columns.str.lower().str.strip().str.replace(" ", "_")
    except Exception:
        # safe fallback
        jobs.columns = [str(c).lower().strip().replace(" ", "_") for c in jobs.columns]

    if 'location' not in jobs.columns:
        st.error("❌ Missing required column: 'location'. Your CSV columns are:")
        st.write(list(jobs.columns))
        st.stop()

    jobs['location'] = jobs['location'].astype(str).str.strip().str.lower()
    client_col = next((c for c in jobs.columns if 'client' in c), None)
    if client_col:
        jobs['client'] = jobs[client_col]
    else:
        jobs['client'] = "Unknown Client"

    st.success(f"CSV loaded: {len(jobs)} rows. Columns: {list(jobs.columns)}")

    # ---- Search UI ----
    st.markdown("### 🔍 Search Jobs Near You")
    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        search_type = st.radio("Search by", ["City", "ZIP Code"], horizontal=True)
    with col2:
        query = st.text_input("Enter City or ZIP", "").strip()
    with col3:
        radius = st.slider("Radius (miles)", 1, 100, 25)

    if st.button("🔎 Find Jobs", use_container_width=True):
        # basic validation
        if not query:
            st.warning("Please enter a city or ZIP code.")
            st.stop()

        # get user coordinates
        if search_type == "ZIP Code":
            if not query.isdigit() or len(query) != 5:
                st.error("Please enter a valid 5-digit ZIP code.")
                st.stop()
            user_coords = ZIP_COORDS.get(query)
        else:
            user_coords = get_coords(query)

        if not user_coords:
            st.error("⚠️ Could not find that city or ZIP in California. Try a different spelling.")
            st.stop()

        # compute coords for jobs
        try:
            jobs["coords"] = jobs["location"].apply(get_coords)
        except Exception:
            st.error("Error while matching job locations to coordinates.")
            st.text(traceback.format_exc())
            st.stop()

        missing = jobs["coords"].isna().sum()
        if missing > 0:
            st.warning(f"{missing} job(s) not matched to any city and will be excluded.")

        jobs = jobs.dropna(subset=["coords"])
        # guard empty
        if jobs.empty:
            st.warning("No jobs had valid coordinates after matching.")
            st.stop()

        # compute distance
        try:
            jobs["distance"] = jobs["coords"].apply(lambda c: haversine(user_coords, c))
        except Exception:
            st.error("Error computing distances.")
            st.text(traceback.format_exc())
            st.stop()

        nearby = jobs[jobs["distance"] <= radius].sort_values("distance")

        # results
        if nearby.empty:
            st.warning(f"No jobs found within {radius} miles of {query}.")
        else:
            st.success(f"🎯 Found {len(nearby)} job(s) within {radius} miles!")
            for _, row in nearby.iterrows():
                client = row.get("client", "Unknown Client")
                loc = row.get("location", "Unknown Location")
                dist = row["distance"]
                header = f"🏥 {client} — {loc} ({dist:.1f} miles)"
                with st.expander(header):
                    st.markdown(f"""
                    <div class='job-card'>
                        <h4>🏥 {client}</h4>
                        <p><b>📍 Location:</b> {loc}</p>
                        <p><b>📏 Distance:</b> {dist:.1f} miles</p>
                        <p><b>👥 Positions:</b> {row.get('positions', 'N/A')}</p>
                        <p><b>🗣️ Language:</b> {row.get('language', 'N/A')}</p>
                        <p><b>💰 Pay Rate:</b> {row.get('pay_rate', 'N/A')}</p>
                        <p><b>🕒 Schedule:</b> {row.get('schedule', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)

            # show map if coords exist
            try:
                coords_list = [c for c in nearby["coords"] if isinstance(c, (list, tuple)) and len(c) == 2]
                if coords_list:
                    map_df = pd.DataFrame([{"lat": c[0], "lon": c[1]} for c in coords_list])
                    st.subheader("🗺️ Job Locations")
                    st.map(map_df)
                else:
                    st.info("No valid coordinates to show on map.")
            except Exception:
                st.error("Error preparing map.")
                st.text(traceback.format_exc())
