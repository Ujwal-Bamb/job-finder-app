import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import requests
import chardet
from io import StringIO
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide")

# ------------------ Enhanced Custom CSS ------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #e0f2ff, #f5f7ff);
    font-family: 'Segoe UI', sans-serif;
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

# ------------------ Load Data ------------------
@st.cache_data(show_spinner=False, ttl=3600)
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


@st.cache_data(show_spinner=False)
def load_default_jobs():
    url = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/job_finder.csv"
    try:
        # Detect encoding dynamically
        response = requests.get(url)
        raw_data = response.content
        detected = chardet.detect(raw_data)
        encoding = detected["encoding"] or "utf-8"
        return pd.read_csv(StringIO(raw_data.decode(encoding)), on_bad_lines="skip")
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()


CA_CITIES, ZIP_COORDS = load_ca_data()
jobs = load_default_jobs()

# ------------------ Coordinate Resolver ------------------
def get_coords(name):
    if not name:
        return None
    name = str(name).strip().lower()
    zip_match = re.search(r"\b\d{5}\b", name)
    if zip_match:
        z = zip_match.group()
        if z in ZIP_COORDS:
            return ZIP_COORDS[z]
    base_name = name.split(",")[0].strip()
    if base_name in CA_CITIES:
        return CA_CITIES[base_name]
    match = get_close_matches(base_name, CA_CITIES.keys(), n=1, cutoff=0.75)
    return CA_CITIES[match[0]] if match else None


# ------------------ Distance Calculator ------------------
def haversine(c1, c2):
    if not c1 or not c2:
        return float('inf')
    R = 3958.8  # miles
    lat1, lon1 = map(radians, c1)
    lat2, lon2 = map(radians, c2)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ------------------ Main Interface ------------------
st.title("😊 Keep Smiling Job Finder")
st.write("Search caregiver job listings by city or ZIP code in California.")

# Clean up columns
jobs.columns = jobs.columns.str.lower().str.strip().str.replace(" ", "_")
if 'location' not in jobs.columns:
    st.error("❌ Missing required column: 'location'")
    st.stop()
jobs['location'] = jobs['location'].astype(str).str.strip().str.lower()
client_col = next((c for c in jobs.columns if 'client' in c), None)
jobs['client'] = jobs[client_col] if client_col else "Unknown Client"

# ------------------ Search UI ------------------
st.markdown("### 🔍 Search Jobs Near You")
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    search_type = st.radio("Search by", ["City", "ZIP Code"], horizontal=True)
with col2:
    query = st.text_input("Enter City or ZIP", "").strip()
with col3:
    radius = st.slider("Radius (miles)", 1, 100, 25)

# Trigger search when Enter pressed OR button clicked
search_triggered = query != "" or st.button("🔎 Find Jobs", use_container_width=True)

if search_triggered:
    if not query:
        st.warning("Please enter a city or ZIP code.")
        st.stop()

    if search_type == "ZIP Code":
        if not query.isdigit() or len(query) != 5:
            st.error("Please enter a valid 5-digit ZIP code.")
            st.stop()
        user_coords = ZIP_COORDS.get(query)
    else:
        user_coords = get_coords(query)

    if not user_coords:
        st.error("⚠️ Could not find that city or ZIP in California.")
        st.stop()

    # Resolve coordinates for all jobs
    if "coords" not in jobs.columns:
        jobs["coords"] = jobs["location"].apply(get_coords)

    missing = jobs["coords"].isna().sum()
    if missing > 0:
        st.warning(f"{missing} job(s) not matched to any city (excluded).")

    jobs = jobs.dropna(subset=["coords"])
    jobs["distance"] = jobs["coords"].apply(lambda c: haversine(user_coords, c))

    nearby = jobs[jobs["distance"] <= radius].sort_values("distance")

    # ------------------ Results Display ------------------
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
                    <p><b>🗣️ Language:</b> {row.get('language', 'N/A')}</p>
                    <p><b>💰 Pay Rate:</b> {row.get('pay_rate', 'N/A')}</p>
                    <p><b>🕒 Schedule:</b> {row.get('schedule', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

        # ------------------ Interactive Map ------------------
        st.subheader("🗺️ Job Locations")
        map_df = pd.DataFrame([{"lat": c[0], "lon": c[1]} for c in nearby["coords"]])
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position='[lon, lat]',
            get_color='[37, 99, 235, 180]',
            get_radius=600,
        )
        view_state = pdk.ViewState(latitude=user_coords[0], longitude=user_coords[1], zoom=7)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))
