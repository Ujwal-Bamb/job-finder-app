import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

st.set_page_config(page_title="Job Finder", layout="wide")

# ------------------ Geocoding ------------------
@st.cache_data(show_spinner=False)
def geocode_location(location_str):
    """Try to get (lat, lon) for ZIP or city,state."""
    geolocator = Nominatim(user_agent="job_finder_app")
    try:
        loc = geolocator.geocode(location_str)
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None

# ------------------ Distance ------------------
def compute_distance(coord1, coord2):
    try:
        return geodesic(coord1, coord2).miles
    except:
        return None

# ------------------ Main UI ------------------
st.title("😊 Keep Smiling Job Finder")
st.write("Find your next job closer to home 💼")

uploaded_file = st.file_uploader("Upload your jobs CSV", type=['csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.sidebar.header("Candidate Location")
    zip_code = st.sidebar.text_input("ZIP Code")
    city = st.sidebar.text_input("City")
    state = st.sidebar.text_input("State (2-letter)")
    radius = st.sidebar.slider("Radius (miles)", 10, 200, 50)
    find_btn = st.sidebar.button("Find Jobs")

    if find_btn:
        # 1️⃣ Candidate location
        candidate_coords = None
        if zip_code:
            candidate_coords = geocode_location(f"{zip_code}, USA")
        if not candidate_coords and city and state:
            candidate_coords = geocode_location(f"{city}, {state}, USA")
        if not candidate_coords:
            st.error("Invalid ZIP or City + State. Try again.")
            st.stop()

        st.info("📍 Geocoding job locations...")

        # 2️⃣ Job locations
        df['Job_LatLon'] = df['Job Location'].apply(lambda x: geocode_location(str(x)))
        df = df.dropna(subset=['Job_LatLon']).reset_index(drop=True)

        if df.empty:
            st.warning("No valid job locations found in CSV.")
            st.stop()

        # 3️⃣ Compute distances
        df['Distance'] = df['Job_LatLon'].apply(lambda x: compute_distance(candidate_coords, x))
        filtered = df[df['Distance'] <= radius].sort_values('Distance')

        if filtered.empty:
            st.warning(f"No jobs found within {radius} miles.")
        else:
            st.success(f"Found {len(filtered)} job(s) within {radius} miles!")

            # 4️⃣ Show job cards
            for idx, job in filtered.iterrows():
                with st.expander(f"{job['Job Title']} ({job['Job Location']}) — {job['Distance']:.1f} mi"):
                    for col in filtered.columns:
                        if col not in ['Job_LatLon', 'Distance']:
                            st.write(f"**{col}:** {job[col]}")

            # 5️⃣ Map
            map_df = filtered['Job_LatLon'].apply(pd.Series)
            map_df.columns = ['lat', 'lon']
            st.map(map_df)

else:
    st.info("Upload a CSV to start searching.")
