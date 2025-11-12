# app.py
import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches
import traceback

# ----------- Streamlit Setup -----------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide", page_icon="😊")

# ----------- Enhanced Custom CSS -----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #e0f2ff, #f5f7ff);
    font-family: 'Segoe UI', sans-serif;
}
.center-welcome {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 89vh;
    width: 100%;
}
.big-btn button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 18px 50px !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 18px rgba(37,99,235,0.13);
    margin-top: 34px;
    border: none !important;
}
.big-btn button:hover {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    transform: scale(1.07);
}
div[data-testid="stExpander"] {
    background: linear-gradient(145deg, #f8fbff, #e6f0ff);
    border: 1px solid #bfdbfe;
    border-radius: 15px;
    box-shadow: 0 6px 12px rgba(37,99,235,0.1);
    margin-bottom: 15px;
    overflow: hidden;
}
div[data-testid="stExpander"] div[role="button"] {
    background: linear-gradient(135deg, #60a5fa, #3b82f6);
    border-radius: 15px 15px 0 0;
    color: white !important;
    font-weight: 600;
    padding: 14px 18px !important;
    font-size: 17px;
}
div[data-testid="stExpander"] p {
    color: #1e293b;
}
.job-card {
    background: white;
    border-radius: 12px;
    padding: 18px;
    margin: 10px 0;
    box-shadow: 0 4px 10px rgba(37,99,235,0.1);
}
.job-card h4 {
    color: #1e3a8a;
    margin-bottom: 8px;
}
.job-card p {
    margin: 4px 0;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

# ----------- Streamlit Page State -----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# Utility: safe float conversion for lat/lon
def to_float_tuple(v):
    try:
        return (float(v[0]), float(v[1]))
    except Exception:
        return None

# ----------- Welcome Page -----------
if st.session_state.page == "welcome":
    st.markdown(
        """
        <div style="text-align:center">
            <h1>😊 Keep Smiling Job Finder</h1>
            <h3>💼 Find your next job closer to home</h3>
            <img src="https://media.giphy.com/media/xT1R9I7Ne3mAQhXcWc/giphy.gif" width="260" style="border-radius:12px; margin:25px 0;">
            <p style="font-size:18px; color:#1e293b;">
                Upload your job list and discover nearby opportunities instantly!
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Let's Start", key="start-main"):
            st.session_state.page = "main"
            st.experimental_rerun()

# ----------- Main App Page -----------
elif st.session_state.page == "main":
    st.title("😊 Keep Smiling Job Finder")
    st.write("Search caregiver job listings by city or ZIP code in California.")

    # --- Load California city/ZIP data ---
    @st.cache_data(ttl=3600)
    def load_ca_data():
        """
        Expects a CSV with columns: city, lat, lng, zips (space-separated)
        Returns: (cities_dict, zip_dict)
        """
        url = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/california_cities_minimal.csv"
        df = pd.read_csv(url)
        df = df.fillna("")  # avoid NaN when splitting zips
        cities = {}
        zips = {}
        for _, row in df.iterrows():
            city_name = str(row.get('city', '')).strip().lower()
            try:
                lat = float(row.get('lat', None))
                lng = float(row.get('lng', None))
            except Exception:
                continue
            if city_name:
                cities[city_name] = (lat, lng)

            zips_str = str(row.get('zips', '')).strip()
            if zips_str:
                for z in zips_str.split():
                    z_clean = z.strip()
                    if z_clean:
                        zips[z_clean] = (lat, lng)
        return cities, zips

    try:
        CA_CITIES, ZIP_COORDS = load_ca_data()
    except Exception as e:
        st.error("Failed to load California city data. See details below.")
        st.exception(e)
        st.stop()

    def get_coords(name: str):
        """Return (lat, lon) tuple for a city name. Tries exact then fuzzy match."""
        if not name:
            return None
        name_key = str(name).strip().lower().split(",")[0]
        if name_key in CA_CITIES:
            return CA_CITIES[name_key]
        # fuzzy match
        matches = get_close_matches(name_key, list(CA_CITIES.keys()), n=1, cutoff=0.70)
        if matches:
            return CA_CITIES[matches[0]]
        return None

    def haversine(c1, c2):
        """Return distance in miles between two (lat, lon) tuples. Returns large number on bad input."""
        if not c1 or not c2:
            return float("inf")
        try:
            R = 3958.8  # miles
            lat1, lon1 = map(radians, c1)
            lat2, lon2 = map(radians, c2)
            dlat, dlon = lat2 - lat1, lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            return R * 2 * atan2(sqrt(a), sqrt(1 - a))
        except Exception:
            return float("inf")

    # --- Upload Jobs CSV ---
    st.markdown("### 📂 Upload Job List")
    file = st.file_uploader("Upload your CSV (columns: client_name, location, language, pay_rate, schedule)", type=["csv"])

    if not file:
        st.info("Please upload a CSV to continue.")
        st.stop()

    # Read CSV safely and normalize columns
    try:
        jobs = pd.read_csv(file)
    except Exception as e:
        st.error("Could not read the uploaded CSV. Make sure it's a valid CSV file.")
        st.exception(e)
        st.stop()

    jobs.columns = jobs.columns.str.lower().str.strip().str.replace(" ", "_", regex=False)

    if 'location' not in jobs.columns:
        st.error("❌ Missing required column: 'location'")
        st.stop()

    jobs['location'] = jobs['location'].astype(str).str.strip().str.lower()

    client_col = next((c for c in jobs.columns if 'client' in c), None)
    if client_col:
        jobs['client'] = jobs[client_col]
    else:
        jobs['client'] = "Unknown Client"

    # --- Search UI ---
    st.markdown("### 🔍 Search Jobs Near You")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_type = st.radio("Search by", ["City", "ZIP Code"], horizontal=True)
    with col2:
        query = st.text_input("Enter City or ZIP", "").strip()
    with col3:
        radius = st.slider("Radius (miles)", 1, 100, 25)

    if st.button("🔎 Find Jobs", use_container_width=True):
        try:
            if not query:
                st.warning("Please enter a city or ZIP code.")
                st.stop()

            # --- Get user coordinates ---
            if search_type == "ZIP Code":
                qstr = str(query).strip()
                if not (qstr.isdigit() and len(qstr) == 5):
                    st.error("Please enter a valid 5-digit ZIP code.")
                    st.stop()
                user_coords = ZIP_COORDS.get(qstr)
            else:
                user_coords = get_coords(query)

            if not user_coords:
                st.error("⚠️ Could not find that city or ZIP in California.")
                st.stop()

            # --- Match job coordinates ---
            # Apply get_coords to each job location (returns tuple or None)
            jobs["coords"] = jobs["location"].apply(get_coords)

            missing = jobs["coords"].isna().sum()
            if missing > 0:
                st.warning(f"{missing} job(s) not matched to any city (they will be excluded).")

            # Keep only matched jobs
            jobs_clean = jobs.dropna(subset=["coords"]).copy()

            # ensure coords are floats
            jobs_clean["coords"] = jobs_clean["coords"].apply(lambda c: to_float_tuple(c))
            jobs_clean = jobs_clean.dropna(subset=["coords"])

            jobs_clean["distance"] = jobs_clean["coords"].apply(lambda c: haversine(user_coords, c))

            nearby = jobs_clean[jobs_clean["distance"] <= radius].sort_values("distance")

            # --- Results ---
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

                st.subheader("🗺️ Job Locations")
                map_df = pd.DataFrame([{"lat": c[0], "lon": c[1]} for c in nearby["coords"]])
                st.map(map_df)

        except Exception as e:
            st.error("An unexpected error occurred while searching jobs. See details below.")
            st.exception(traceback.format_exc())
            st.stop()
