# job_finder_app.py
import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import ast

# --------------------------- Setup ---------------------------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")

# Initialize geolocator
geolocator = Nominatim(user_agent="job_finder_app")

# ----------------------- Helper Functions -----------------------
def geocode_city(city, state="California"):
    """Return (lat, lon) for a city,state"""
    try:
        location = geolocator.geocode(f"{city}, {state}, USA", timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None
    return None

def compute_distance(loc1, loc2):
    """Compute miles between two (lat, lon) tuples"""
    try:
        return geodesic(loc1, loc2).miles
    except:
        return np.inf

def parse_locations(loc_str):
    """Split multi-city strings by comma"""
    if pd.isna(loc_str):
        return []
    loc_str = str(loc_str).strip()
    # Split by comma
    parts = [x.strip() for x in loc_str.split(',') if x.strip()]
    return parts if parts else [loc_str]

def expand_multi_locations(df, col='location'):
    """Expand rows with multiple cities into separate rows"""
    rows = []
    for _, row in df.iterrows():
        locs = parse_locations(row.get(col, ''))
        for loc in locs:
            new_row = row.copy()
            new_row[col] = loc
            rows.append(new_row)
    return pd.DataFrame(rows).reset_index(drop=True)

# ----------------------- Welcome Page -----------------------
def show_welcome_page():
    st.markdown(
        """
        <div style='height:70vh; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
            <h1 style='font-size:4rem;'>😊 Keep Smiling Job Finder</h1>
            <h3>Find your next opportunity closer to home 💼</h3>
            <br>
        </div>
        """, unsafe_allow_html=True
    )
    if st.button("🚀 Get Started"):
        st.session_state.page = 'main'
        st.experimental_rerun()

# ----------------------- Main Page -----------------------
def show_main_page():
    st.header("Search Jobs by Location")
    
    uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])
    if uploaded_file is None:
        st.info("Upload a CSV file to start searching for jobs (must include 'job_title', 'client_name', 'location').")
        return

    df = pd.read_csv(uploaded_file)
    df = expand_multi_locations(df, 'location')

    # Candidate Inputs
    st.sidebar.header("Candidate Location")
    city = st.sidebar.text_input("Enter your City")
    state = st.sidebar.text_input("Enter your State (default: California)", value="California")
    radius = st.sidebar.slider("Search Radius (miles)", 1, 100, 50)
    search_btn = st.sidebar.button("Find Jobs")

    if not search_btn:
        st.info("Enter City+State and click **Find Jobs**.")
        return

    # Geocode candidate
    candidate_loc = geocode_city(city, state)
    if not candidate_loc:
        st.error("Invalid location! Enter a valid City + State.")
        return

    # Geocode jobs
    st.info("📍 Geocoding job locations...")
    job_coords = []
    for loc in df['location']:
        coords = geocode_city(loc, state)
        if coords:
            job_coords.append(coords)
        else:
            job_coords.append(None)
    df['Job_LatLon'] = job_coords
    df = df.dropna(subset=['Job_LatLon']).reset_index(drop=True)

    if df.empty:
        st.warning("No valid job locations found.")
        return

    # Compute distances
    df['Distance'] = df['Job_LatLon'].apply(lambda loc: compute_distance(candidate_loc, loc))
    df_filtered = df[df['Distance'] <= radius].sort_values('Distance').reset_index(drop=True)

    if df_filtered.empty:
        st.warning(f"No jobs found within {radius} miles.")
        return

    # Display job cards
    st.subheader(f"✅ Jobs within {radius} miles:")
    for idx, row in df_filtered.iterrows():
        st.markdown(
            f"""
            <div style='background-color:#6e54f7; padding:15px; border-radius:12px; margin-bottom:10px;
                        transition: transform 0.2s, box-shadow 0.2s; cursor:pointer;'>
                <b style='font-size:1.2rem;'>{row.get('client_name', '')} - {row.get('job_title', '')}</b><br>
                <span style='color:#fff;'>Location: {row['location']}</span><br>
                <span style='color:#fff;'>Distance: {row['Distance']:.1f} miles</span>
            </div>
            """, unsafe_allow_html=True
        )
        with st.expander("Show Details"):
            for col in df_filtered.columns:
                if col not in ['Job_LatLon','Distance']:
                    st.write(f"**{col}:** {row[col]}")

    # Map
    map_data = pd.DataFrame(df_filtered['Job_LatLon'].tolist(), columns=['lat', 'lon'])
    map_data['job_title'] = df_filtered['job_title']
    st.map(map_data)

# ----------------------- Page Navigation -----------------------
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'

if st.session_state.page == 'welcome':
    show_welcome_page()
else:
    show_main_page()
