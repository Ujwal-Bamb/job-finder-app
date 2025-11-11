import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# 🎨 PAGE CONFIGURATION
st.set_page_config(page_title="Keep Smiling 😊 Job Finder", page_icon="😊", layout="wide")

# 🌟 HEADER
st.markdown("""
    <div style='text-align:center; padding:20px; background-color:#f0f9ff; border-radius:15px;'>
        <h1 style='color:#2E86C1;'>Keep Smiling 😊 Nearby Job Finder</h1>
        <h4>Find jobs within 40 miles of your ZIP code</h4>
    </div>
""", unsafe_allow_html=True)

# 📍 INPUTS
st.sidebar.header("🔍 Candidate Details")
candidate_zip = st.sidebar.text_input("Enter Candidate ZIP Code:", "10001")
max_distance = st.sidebar.slider("Maximum distance (miles):", 5, 100, 40)

# 📋 JOB DATA INPUT
st.sidebar.header("💼 Job Data Upload")
st.sidebar.markdown("Upload a CSV with columns like: **ClientName, City, State, GenderRequired, LanguageRequired**")
uploaded_file = st.sidebar.file_uploader("Choose your job CSV file", type=["csv"])

# 🌎 FUNCTION TO GET LAT/LONG
geolocator = Nominatim(user_agent="job_finder_app")

def get_lat_lon_from_zip(zip_code):
    try:
        location = geolocator.geocode(zip_code)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None
    return None

def get_lat_lon_from_city_state(city, state):
    try:
        location = geolocator.geocode(f"{city}, {state}")
        if location:
            return (location.latitude, location.longitude)
    except:
        return None
    return None

# 💾 PROCESS JOB DATA
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)

    if {'City', 'State'}.issubset(jobs_df.columns):
        candidate_coords = get_lat_lon_from_zip(candidate_zip)
        if not candidate_coords:
            st.error("Could not find location for the ZIP code. Please try again.")
        else:
            jobs_df["Coordinates"] = jobs_df.apply(lambda row: get_lat_lon_from_city_state(row["City"], row["State"]), axis=1)
            jobs_df = jobs_df.dropna(subset=["Coordinates"])
            jobs_df["Distance_miles"] = jobs_df["Coordinates"].apply(lambda x: geodesic(candidate_coords, x).miles)

            nearby_jobs = jobs_df[jobs_df["Distance_miles"] <= max_distance]

            st.success(f"✅ Found {len(nearby_jobs)} jobs within {max_distance} miles.")

            st.dataframe(nearby_jobs)

            # 🗺️ SHOW MAP
            m = folium.Map(location=candidate_coords, zoom_start=9)
            folium.Marker(candidate_coords, tooltip="Candidate Location", icon=folium.Icon(color="blue")).add_to(m)
            for _, row in nearby_jobs.iterrows():
                folium.Marker(row["Coordinates"], tooltip=f"{row['City']}, {row['State']}", icon=folium.Icon(color="green")).add_to(m)

            st_folium(m, width=700, height=500)
    else:
        st.error("CSV must contain 'City' and 'State' columns.")
else:
    st.info("👈 Upload a CSV file to find nearby jobs.")
