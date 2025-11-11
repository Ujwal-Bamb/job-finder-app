# job_finder_california.py
import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# ------------------ Setup ------------------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
st.title("😊 Keep Smiling Job Finder")
st.write("Find your next job closer to home 💼")

# Initialize geolocator
geolocator = Nominatim(user_agent="job_finder_app")

# ------------------ Helper Functions ------------------
def geocode_location(location_str):
    """Return (lat, lon) for a ZIP code or city in California"""
    if not location_str:
        return None
    try:
        loc = geolocator.geocode(f"{location_str}, California, USA", timeout=10)
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None

def compute_distance(loc1, loc2):
    """Distance in miles between two (lat, lon) tuples"""
    try:
        return geodesic(loc1, loc2).miles
    except:
        return np.inf

def parse_locations(loc_str):
    """Split multi-city locations in CSV"""
    if pd.isna(loc_str):
        return []
    return [x.strip() for x in str(loc_str).split(',') if x.strip()]

def expand_multi_locations(df, col='location'):
    rows = []
    for _, row in df.iterrows():
        locs = parse_locations(row.get(col, ''))
        for loc in locs:
            new_row = row.copy()
            new_row[col] = loc
            rows.append(new_row)
    return pd.DataFrame(rows).reset_index(drop=True)

# ------------------ Upload CSV ------------------
uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = expand_multi_locations(df, 'location')

    # ------------------ Candidate Input ------------------
    st.sidebar.header("Enter your location")
    city_or_zip = st.sidebar.text_input("Enter City or ZIP code")
    radius = st.sidebar.slider("Search Radius (miles)", 1, 100, 50)
    search_btn = st.sidebar.button("Find Jobs")

    if search_btn:
        candidate_loc = geocode_location(city_or_zip)
        if not candidate_loc:
            st.error("Invalid location! Enter a valid City or ZIP code in California.")
        else:
            # ------------------ Geocode Jobs ------------------
            st.info("📍 Geocoding job locations...")
            df['Job_LatLon'] = df['location'].apply(lambda x: geocode_location(x))
            df = df.dropna(subset=['Job_LatLon']).reset_index(drop=True)

            if df.empty:
                st.warning("No valid job locations found.")
            else:
                # ------------------ Compute distances ------------------
                df['Distance'] = df['Job_LatLon'].apply(lambda loc: compute_distance(candidate_loc, loc))
                df_filtered = df[df['Distance'] <= radius].sort_values('Distance').reset_index(drop=True)

                if df_filtered.empty:
                    st.warning(f"No jobs found within {radius} miles.")
                else:
                    # ------------------ Display Jobs ------------------
                    st.subheader(f"✅ Jobs within {radius} miles of {city_or_zip}:")
                    for idx, row in df_filtered.iterrows():
                        st.markdown(
                            f"""
                            <div style='background-color:#6e54f7; padding:15px; border-radius:12px; margin-bottom:10px;
                                        transition: transform 0.2s, box-shadow 0.2s; cursor:pointer;'>
                                <b style='font-size:1.2rem;'>{row.get('client_name','')} - {row.get('job_title','')}</b><br>
                                <span style='color:#fff;'>Location: {row['location']}</span><br>
                                <span style='color:#fff;'>Distance: {row['Distance']:.1f} miles</span>
                            </div>
                            """, unsafe_allow_html=True
                        )
                        with st.expander("Show Details"):
                            for col in df_filtered.columns:
                                if col not in ['Job_LatLon','Distance']:
                                    st.write(f"**{col}:** {row[col]}")

                    # ------------------ Map ------------------
                    map_data = pd.DataFrame(df_filtered['Job_LatLon'].tolist(), columns=['lat', 'lon'])
                    map_data['job_title'] = df_filtered['job_title']
                    st.map(map_data)
else:
    st.info("Upload a CSV file with job listings to start searching.")
