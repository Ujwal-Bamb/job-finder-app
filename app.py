import streamlit as st
import pandas as pd
import numpy as np
import ast
import time
from uszipcode import SearchEngine
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from functools import lru_cache

# Initialize geolocator and ZIP code search engine
search = SearchEngine(simple_zipcode=True)
geolocator = Nominatim(user_agent="keep_smiling_job_finder")

# Cache results for faster performance
@st.cache_data
def get_lat_lon_zip(zipcode):
    result = search.by_zipcode(zipcode)
    if result and result.zipcode:
        return (result.lat, result.lng)
    return None

@st.cache_data
def get_lat_lon_city_state(city_state):
    try:
        location = geolocator.geocode(city_state)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None

# Parse multi-location strings into list
def parse_locations(loc_str):
    if pd.isna(loc_str):
        return []
    loc_str = loc_str.strip()
    if loc_str.startswith('[') and loc_str.endswith(']'):
        try:
            loc_list = ast.literal_eval(loc_str)
            if isinstance(loc_list, list):
                return [x.strip() for x in loc_list if x.strip()]
        except:
            pass
    if ',' in loc_str:
        return [x.strip() for x in loc_str.split(',') if x.strip()]
    if '/' in loc_str:
        return [x.strip() for x in loc_str.split('/') if x.strip()]
    return [loc_str]

# Distance in miles
def compute_distance(loc1, loc2):
    try:
        return geodesic(loc1, loc2).miles
    except:
        return np.inf

# ----------------- CSS STYLES -----------------
WELCOME_STYLE = '''
<style>
body, html, #root {height: 100%; margin:0; overflow:hidden; font-family: 'Segoe UI', sans-serif;}
.welcome-page {height:100vh; width:100vw; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; color:white;
background: linear-gradient(-45deg, #ff6b6b, #556270, #c7f464, #ff6b6b); background-size:400% 400%; animation: gradientBG 15s ease infinite;}
@keyframes gradientBG {0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}
.button-start {margin-top:2rem; font-size:1.8rem; padding:1rem 3rem; cursor:pointer; border:none; border-radius:50px; background:linear-gradient(90deg, #21d4fd 0%, #b721ff 100%); color:white; box-shadow:0 0 15px rgba(183,33,255,0.6); transition:all 0.3s ease;}
.button-start:hover {box-shadow:0 0 25px rgba(183,33,255,0.9); transform:scale(1.05);}
h1 {font-size:4rem; margin:0;}
h2 {font-size:1.75rem; font-weight:normal; margin-top:0.5rem; color:#eee;}
</style>
'''

JOB_CARD_STYLE = '''
<style>
.job-card {background-color:#121212; border-radius:12px; padding:1rem 1.5rem; margin:1rem 0; color:#eee; cursor:pointer; transition:transform 0.15s, box-shadow 0.15s; box-shadow:0 2px 6px rgba(0,0,0,0.7);}
.job-card:hover {box-shadow:0 6px 20px rgba(183,33,255,0.8); transform:translateY(-5px);}
.job-card-title {font-size:1.3rem; font-weight:600;}
.job-card-subtitle {font-size:1rem; color:#b721ff; margin-top:0.3rem;}
.job-card-distance {font-size:0.9rem; font-weight:500; color:#66ffcc; margin-top:0.5rem;}
.details {margin-top:0.8rem; font-size:0.9rem; color:#ddd; white-space: pre-line;}
</style>
'''

st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")

# Welcome page state
if 'welcome_done' not in st.session_state:
    st.session_state.welcome_done = False
    st.session_state.start_time = time.time()

def show_welcome():
    st.markdown(WELCOME_STYLE, unsafe_allow_html=True)
    st.markdown('<div class="welcome-page">', unsafe_allow_html=True)
    st.markdown('<h1>😊 Keep Smiling Job Finder</h1>', unsafe_allow_html=True)
    st.markdown('<h2>Find your next opportunity closer to home 💼</h2>', unsafe_allow_html=True)
    if st.button("🚀 Let's Start"):
        st.session_state.welcome_done = True
    st.markdown('</div>', unsafe_allow_html=True)
    # Auto skip after 2s
    if time.time() - st.session_state.start_time > 2:
        st.session_state.welcome_done = True

if not st.session_state.welcome_done:
    show_welcome()
else:
    st.markdown(JOB_CARD_STYLE, unsafe_allow_html=True)
    st.title("Keep Smiling Job Finder")
    uploaded_file = st.file_uploader("Upload your jobs CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        # Expand multi-locations
        rows = []
        for _, row in df.iterrows():
            locs = parse_locations(row.get('Location', ''))
            for loc in locs:
                new_row = row.copy()
                new_row['Location'] = loc
                rows.append(new_row)
        df_expanded = pd.DataFrame(rows)

        # Candidate input
        st.sidebar.header("Candidate Location")
        zip_code = st.sidebar.text_input("Enter ZIP code (optional):", max_chars=5)
        city = st.sidebar.text_input("Or enter City:")
        state = st.sidebar.text_input("State:")
        radius = st.sidebar.slider("Search Radius (miles)", min_value=1, max_value=100, value=40)

        # Candidate lat/lon
        candidate_latlon = None
        if zip_code.isdigit() and len(zip_code)==5:
            candidate_latlon = get_lat_lon_zip(zip_code)
        if not candidate_latlon and city and state:
            candidate_latlon = get_lat_lon_city_state(f"{city}, {state}")

        if candidate_latlon is None:
            st.error("Invalid or missing candidate location. Please provide valid ZIP or City + State.")
            st.stop()

        # Compute job lat/lon
        df_expanded['Job_LatLon'] = df_expanded['Location'].apply(lambda x: get_lat_lon_city_state(x))
        df_expanded = df_expanded.dropna(subset=['Job_LatLon']).reset_index(drop=True)
        df_expanded['Distance'] = df_expanded['Job_LatLon'].apply(lambda x: compute_distance(candidate_latlon, x))
        df_filtered = df_expanded[df_expanded['Distance'] <= radius].sort_values('Distance').reset_index(drop=True)

        if df_filtered.empty:
            st.warning(f"No jobs found within {radius} miles of your location.")
        else:
            st.markdown(f"### Jobs within {radius} miles:")
            for idx, row in df_filtered.iterrows():
                st.markdown(f'''
                <div class="job-card">
                    <div class="job-card-title">{row.get('Client', '')} - {row.get('Job_Title', '')}</div>
                    <div class="job-card-subtitle">{row.get('Location', '')}</div>
                    <div class="job-card-distance">Distance: {row['Distance']:.1f} miles</div>
                </div>
                ''', unsafe_allow_html=True)
                with st.expander("Show Details", expanded=False):
                    details = ""
                    for col in df_filtered.columns:
                        if col not in ['Job_LatLon','Distance']:
                            details += f"{col}: {row.get(col,'')}\n"
                    st.text(details)
    else:
        st.info("Please upload a CSV file with job listings to start searching.")
