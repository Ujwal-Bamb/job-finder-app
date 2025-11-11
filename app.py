import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# --------------------------- Geocoding ---------------------------
geolocator = Nominatim(user_agent="keep_smiling_job_finder")

@st.cache_data(show_spinner=False)
def geocode_location(location_str):
    try:
        loc = geolocator.geocode(location_str)
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None

def compute_distance(loc1, loc2):
    try:
        return geodesic(loc1, loc2).miles
    except:
        return np.inf

def parse_locations(loc_str):
    if pd.isna(loc_str):
        return []
    loc_str = str(loc_str).strip()
    if loc_str.startswith('[') and loc_str.endswith(']'):
        try:
            import ast
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

# --------------------------- Welcome Page ---------------------------
WELCOME_STYLE = '''
<style>
body, html, #root {height:100%; margin:0; font-family:sans-serif;}
.welcome-container {
    height:100vh; width:100vw; display:flex; flex-direction:column; justify-content:center; align-items:center;
    text-align:center; color:white; 
    background: linear-gradient(120deg,#ff416c,#ff4b2b,#1f4037,#99f2c8);
    background-size: 400% 400%; animation: gradientBG 15s ease infinite;
}
@keyframes gradientBG {
0% {background-position:0% 50%;}
50% {background-position:100% 50%;}
100% {background-position:0% 50%;}
}
.welcome-title {font-size:4rem; font-weight:700; margin:0;}
.welcome-subtitle {font-size:1.8rem; margin-top:1rem; font-weight:400;}
.start-button {
    margin-top:2rem; padding:1rem 3rem; font-size:1.5rem; font-weight:600; border:none; border-radius:50px;
    cursor:pointer; background: linear-gradient(90deg,#1e3c72,#2a5298); color:white;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.start-button:hover {transform:scale(1.05); box-shadow:0 0 20px rgba(0,0,0,0.5);}
</style>
'''

def show_welcome():
    st.markdown(WELCOME_STYLE, unsafe_allow_html=True)
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<div class="welcome-title">😊 Keep Smiling Job Finder</div>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-subtitle">Find your next job closer to home</div>', unsafe_allow_html=True)
    if st.button("🚀 Get Started"):
        st.session_state.page = "search"
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------- Job Card Styles ---------------------------
JOB_CARD_STYLE = '''
<style>
.job-card {background-color:#1e1e1e; border-radius:12px; padding:1rem 1.5rem; margin:1rem 0; color:white; cursor:pointer;
transition: transform 0.2s ease, box-shadow 0.2s ease; border-left:5px solid #6e54f7;}
.job-card:hover {transform:translateY(-5px); box-shadow:0 8px 20px rgba(110,84,247,0.5);}
.job-title {font-size:1.3rem; font-weight:700; color:#6e54f7;}
.job-client {font-size:1.1rem; color:#ffbc42;}
.job-location {font-style:italic; color:#66ffcc;}
.job-distance {font-weight:600; color:#82e8a2;}
</style>
'''

# --------------------------- Main Search Page ---------------------------
def show_search_page():
    st.markdown(JOB_CARD_STYLE, unsafe_allow_html=True)
    st.title("Keep Smiling Job Finder - Search Jobs")

    uploaded_file = st.file_uploader("Upload Jobs CSV", type=["csv"])
    if not uploaded_file:
        st.info("Upload a CSV file to start searching jobs.")
        return

    df = pd.read_csv(uploaded_file)
    # Expand multi-locations
    expanded_rows = []
    for _, row in df.iterrows():
        locations = parse_locations(row.get('Location',''))
        for loc in locations:
            new_row = row.copy()
            new_row['Location'] = loc
            expanded_rows.append(new_row)
    df_expanded = pd.DataFrame(expanded_rows)

    st.sidebar.header("Candidate Location")
    zip_code = st.sidebar.text_input("ZIP code (optional)")
    city = st.sidebar.text_input("City (optional)")
    state = st.sidebar.text_input("State (optional)")
    radius = st.sidebar.slider("Search Radius (miles)", min_value=1, max_value=200, value=50)

    if st.sidebar.button("Find Jobs"):
        # Determine candidate coordinates
        candidate_loc = None
        if zip_code:
            candidate_loc = geocode_location(zip_code)
        if not candidate_loc and city and state:
            candidate_loc = geocode_location(f"{city}, {state}")
        if not candidate_loc:
            st.error("Invalid location! Enter a valid ZIP or City+State.")
            return

        # Geocode job locations
        df_expanded['Job_LatLon'] = df_expanded['Location'].apply(lambda x: geocode_location(x))
        df_expanded = df_expanded.dropna(subset=['Job_LatLon']).reset_index(drop=True)

        # Compute distance
        df_expanded['Distance'] = df_expanded['Job_LatLon'].apply(lambda loc: compute_distance(candidate_loc, loc))
        filtered = df_expanded[df_expanded['Distance'] <= radius].sort_values(by='Distance').reset_index(drop=True)

        if filtered.empty:
            st.warning(f"No jobs found within {radius} miles of your location.")
            return

        st.success(f"Found {len(filtered)} jobs within {radius} miles!")

        # Show map
        map_center = candidate_loc
        job_map = folium.Map(location=map_center, zoom_start=8)
        folium.Marker(location=candidate_loc, popup="You", icon=folium.Icon(color="blue")).add_to(job_map)
        for _, row in filtered.iterrows():
            folium.Marker(location=row['Job_LatLon'], 
                          popup=f"{row.get('Client','')} - {row.get('Job_Title','')}\n{row.get('Location','')}",
                          icon=folium.Icon(color="purple")).add_to(job_map)
        st_folium(job_map, width=700, height=400)

        # Show job cards
        for idx, row in filtered.iterrows():
            with st.expander(f"{row.get('Client','')} - {row.get('Job_Title','')} ({row['Distance']:.1f} mi)"):
                for col in filtered.columns:
                    if col not in ['Job_LatLon','Distance']:
                        st.write(f"{col}: {row.get(col,'')}")

# --------------------------- Page Control ---------------------------
if 'page' not in st.session_state:
    st.session_state.page = "welcome"

if st.session_state.page == "welcome":
    show_welcome()
else:
    show_search_page()
