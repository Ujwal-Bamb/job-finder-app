import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Initialize geolocator
geolocator = Nominatim(user_agent="keep_smiling_job_finder")

# ------------------ Geocoding ------------------
@st.cache_data
def geocode_location(location_str):
    """Return (lat, lon) for ZIP code or City, State"""
    try:
        loc = geolocator.geocode(location_str)
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None

# ------------------ Distance ------------------
def compute_distance(loc1, loc2):
    try:
        return geodesic(loc1, loc2).miles
    except:
        return np.inf

# ------------------ Multi-location parser ------------------
def parse_locations(loc_str):
    if pd.isna(loc_str):
        return []
    loc_str = str(loc_str).strip()
    if loc_str.startswith('[') and loc_str.endswith(']'):
        import ast
        try:
            lst = ast.literal_eval(loc_str)
            if isinstance(lst, list):
                return [x.strip() for x in lst if x.strip()]
        except:
            pass
    # Split by comma or slash
    if '/' in loc_str:
        return [x.strip() for x in loc_str.split('/') if x.strip()]
    if ',' in loc_str:
        parts = [x.strip() for x in loc_str.split(',') if x.strip()]
        if len(parts) > 1:
            return [", ".join(parts[i:i+2]) for i in range(0, len(parts), 2)]
        return parts
    return [loc_str]

# ------------------ Welcome Page ------------------
WELCOME_STYLE = '''
<style>
body, html, #root {height:100%; margin:0; font-family:sans-serif;}
.welcome-container {
    display:flex;
    justify-content:center;
    align-items:center;
    height:100vh;
    width:100vw;
    flex-direction:column;
    background: linear-gradient(120deg,#ff416c,#ff4b2b,#1f4037,#99f2c8);
    background-size:400% 400%;
    animation: gradientBG 15s ease infinite;
    color:white;
    text-align:center;
}
@keyframes gradientBG {
0% {background-position:0% 50%;}
50% {background-position:100% 50%;}
100% {background-position:0% 50%;}
}
.welcome-title {font-size:4rem; font-weight:700; margin:0;}
.welcome-subtitle {font-size:1.8rem; margin-top:1rem;}
.start-button {
    margin-top:3rem;
    padding:1rem 3rem;
    font-size:1.5rem;
    font-weight:600;
    border:none;
    border-radius:50px;
    cursor:pointer;
    background: linear-gradient(90deg,#1e3c72,#2a5298);
    color:white;
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
    if st.button("🚀 Get Started", key="welcome_start"):
        st.session_state.welcome_done = True
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------ Job Card Style ------------------
JOB_CARD_STYLE = '''
<style>
.job-card {background: linear-gradient(135deg,#ff7e5f,#feb47b); border-radius:15px; padding:15px; margin:10px 0;
cursor:pointer; transition: transform 0.3s, box-shadow 0.3s;}
.job-card:hover {transform: translateY(-5px); box-shadow:0 8px 20px rgba(0,0,0,0.5);}
.job-title {font-size:1.3rem; font-weight:700; color:#fff;}
.job-location {font-size:1rem; color:#f0f0f0;}
.job-distance {font-size:0.9rem; color:#00ff99; font-weight:600;}
.details {margin-top:0.8rem; font-size:0.9rem; color:#fff; white-space:pre-line;}
</style>
'''

# ------------------ Main App ------------------
def main_page():
    st.markdown(JOB_CARD_STYLE, unsafe_allow_html=True)
    st.title("Keep Smiling Job Finder")

    # CSV upload
    uploaded_file = st.file_uploader("Upload Jobs CSV", type=["csv"])
    if not uploaded_file:
        st.info("Please upload a CSV file with job listings to start searching.")
        return

    df = pd.read_csv(uploaded_file)

    # Expand multi-location
    expanded_rows = []
    for _, row in df.iterrows():
        for loc in parse_locations(row.get('Location', '')):
            new_row = row.copy()
            new_row['Location'] = loc
            expanded_rows.append(new_row)
    df_expanded = pd.DataFrame(expanded_rows)

    # Candidate input
    st.sidebar.header("Candidate Location")
    zip_code = st.sidebar.text_input("ZIP Code")
    city = st.sidebar.text_input("City")
    state = st.sidebar.text_input("State")
    radius = st.sidebar.slider("Search Radius (miles)", 1, 100, 40)

    # Get candidate lat/lon
    candidate_coords = None
    if zip_code:
        candidate_coords = geocode_location(zip_code)
    if not candidate_coords and city and state:
        candidate_coords = geocode_location(f"{city}, {state}")
    if not candidate_coords:
        st.error("Invalid location. Enter ZIP code or City + State.")
        return

    # Geocode job locations
    df_expanded['Job_LatLon'] = df_expanded['Location'].apply(lambda x: geocode_location(x))
    df_expanded = df_expanded.dropna(subset=['Job_LatLon']).reset_index(drop=True)

    # Compute distance
    df_expanded['Distance'] = df_expanded['Job_LatLon'].apply(lambda x: compute_distance(candidate_coords, x))
    df_filtered = df_expanded[df_expanded['Distance'] <= radius].sort_values('Distance')

    if df_filtered.empty:
        st.warning(f"No jobs found within {radius} miles.")
        return

    # Map view
    map_data = pd.DataFrame({
        'lat': [lat for lat, lon in df_filtered['Job_LatLon']],
        'lon': [lon for lat, lon in df_filtered['Job_LatLon']],
        'title': df_filtered['Job_Title']
    })
    st.map(map_data)

    # Job cards
    for _, row in df_filtered.iterrows():
        with st.expander(f"{row.get('Client','')} - {row.get('Job_Title','')} ({row.get('Location','')}) - {row['Distance']:.1f} mi"):
            details = ""
            for col in df_filtered.columns:
                if col not in ['Job_LatLon', 'Distance']:
                    details += f"{col}: {row.get(col,'')}\n"
            st.text(details)

# ------------------ Session ------------------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
if 'welcome_done' not in st.session_state:
    st.session_state.welcome_done = False

if not st.session_state.welcome_done:
    show_welcome()
else:
    main_page()
