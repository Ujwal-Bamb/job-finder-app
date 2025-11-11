import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# ------------------ Load Jobs ------------------
jobs_df = pd.read_csv("your_jobs_data.csv")  # Ensure it has 'Job Title', 'Client Name', 'Job Location', etc.

# ------------------ Geocoding ------------------
@st.cache_data
def geocode_location(location_str):
    geolocator = Nominatim(user_agent="job_board_app")
    try:
        loc = geolocator.geocode(location_str)
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None

# Pre-geocode all job locations (cached)
@st.cache_data
def geocode_jobs(df):
    df['Job_LatLon'] = df['Job Location'].apply(lambda x: geocode_location(x))
    return df.dropna(subset=['Job_LatLon']).reset_index(drop=True)

# ------------------ Distance Calculation ------------------
def compute_distance(coord1, coord2):
    try:
        return geodesic(coord1, coord2).miles
    except:
        return None

# ------------------ Streamlit UI ------------------
st.header("😊 Welcome to the Job Board!")

user_zip = st.text_input("Enter your ZIP code:")
radius = st.slider("Select search radius (miles):", 10, 100, 25)
search_btn = st.button("Find Jobs")

if search_btn:
    if not user_zip.strip():
        st.error("Please enter a valid ZIP code.")
    else:
        user_coords = geocode_location(user_zip)
        if not user_coords:
            st.error("Invalid ZIP code entered. Please try again.")
        else:
            st.info("📍 Searching jobs near your location...")
            
            # Geocode jobs
            jobs_df_geo = geocode_jobs(jobs_df)

            # Compute distances
            jobs_df_geo['Distance'] = jobs_df_geo['Job_LatLon'].apply(lambda x: compute_distance(user_coords, x))

            # Filter by radius
            filtered_jobs = jobs_df_geo[jobs_df_geo['Distance'] <= radius].sort_values('Distance')

            if filtered_jobs.empty:
                st.warning(f"No jobs found within {radius} miles.")
            else:
                st.success(f"Found {len(filtered_jobs)} job(s) within {radius} miles!")
                for idx, job in filtered_jobs.iterrows():
                    with st.expander(f"{job['Job Title']} ({job['Job Location']}) — {job['Distance']:.1f} mi"):
                        st.write(f"**Client:** {job['Client Name']}")
                        st.write(f"**Agenda:** {job.get('Agenda','N/A')}")
                        st.write(f"**Language:** {job.get('Language','N/A')}")
