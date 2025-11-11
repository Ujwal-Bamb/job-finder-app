import streamlit as st
import pandas as pd
import numpy as np
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from functools import lru_cache

# Initialize geolocator
geolocator = Nominatim(user_agent="keep_smiling_job_finder")

# ------------------- Cache for geocoding -------------------
@st.cache_data(show_spinner=False)
def geocode_location(location_str):
    """Return latitude and longitude for a location string (ZIP, city, or city+state)"""
    try:
        loc = geolocator.geocode(location_str)
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None

# ------------------- Distance calculation -------------------
def compute_distance(loc1, loc2):
    """Return distance in miles between two (lat, lon) tuples"""
    try:
        return geodesic(loc1, loc2).miles
    except:
        return np.inf

# ------------------- Parse multi-location strings -------------------
def parse_locations(loc_str):
    """Handle comma, slash, or list style locations"""
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

# ------------------- Welcome Page -------------------
WELCOME_STYLE = '''
<style>
body,html,#root {height:100%; margin:0; font-family:sans-serif; overflow:hidden;}
.welcome-page {
  height:100vh; width:100vw; display:flex; flex-direction:column; justify-content:center; align-items:center;
  color:white; text-align:center;
  background: linear-gradient(-45deg, #ff6b6b, #556270, #c7f464, #ff6b6b);
  background-size:400% 400%;
  animation: gradientBG 15s ease infinite;
}
@keyframes gradientBG {
  0% {background-position:0% 50%;}
  50% {background-position:100% 50%;}
  100% {background-position:0% 50%;}
}
.button-start {
  margin-top:2rem; font-size:1.8rem; padding:1rem 3rem; cursor:pointer; border:none; border-radius:50px;
  background: linear-gradient(90deg, #21d4fd 0%, #b721ff 100%);
  color:white; box-shadow:0 0 15px rgba(183,33,255,0.6); transition: all 0.3s ease;
}
.button-start:hover { box-shadow:0 0 25px rgba(183,33,255,0.9); transform: scale(1.05);}
h1 {font-size:4rem; margin:0;}
h2 {font-weight:normal; font-size:1.75rem; margin-top:0.5rem; color:#eee;}
</style>
'''

def show_welcome():
    st.markdown(WELCOME_STYLE, unsafe_allow_html=True)
    st.markdown('<div class="welcome-page">', unsafe_allow_html=True)
    st.markdown('<h1>😊 Keep Smiling Job Finder</h1>', unsafe_allow_html=True)
    st.markdown('<h2>Find your next opportunity closer to home 💼</h2>', unsafe_allow_html=True)
    if st.button("🚀 Let's Start"):
        st.session_state.welcome_done = True
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------- Job Card Style -------------------
JOB_CARD_STYLE = '''
<style>
.job-card {background-color:#121212; border-radius:12px; padding:1rem 1.5rem; margin:1rem 0; color:#eee; cursor:pointer; transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out; box-shadow:0 2px 6px rgba(0,0,0,0.7);}
.job-card:hover {box-shadow:0 6px 20px rgba(183,33,255,0.8); transform: translateY(-5px);}
.job-card-title {font-size:1.3rem; font-weight:600;}
.job-card-subtitle {font-size:1rem; color:#b721ff; margin-top:0.3rem;}
.job-card-distance {font-size:0.9rem; font-weight:500; color:#66ffcc; margin-top:0.5rem;}
.details {margin-top:0.8rem; font-size:0.9rem; color:#ddd; white-space:pre-line;}
</style>
'''

# ------------------- Main App -------------------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")

if 'welcome_done' not in st.session_state:
    st.session_state.welcome_done = False

# Show welcome page
if not st.session_state.welcome_done:
    show_welcome()
    st.stop()

# Main app
st.markdown(JOB_CARD_STYLE, unsafe_allow_html=True)
st.title("Keep Smiling Job Finder")

# Upload CSV
uploaded_file = st.file_uploader("Upload your jobs CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Expand multiple locations
    expanded_rows = []
    for _, row in df.iterrows():
        locations = parse_locations(row.get('Location', ''))
        for loc in locations:
            new_row = row.copy()
            new_row['Location'] = loc
            expanded_rows.append(new_row)
    df_expanded = pd.DataFrame(expanded_rows)

    # Candidate Input
    st.sidebar.header("Candidate Location")
    zip_code = st.sidebar.text_input("Enter ZIP code:", max_chars=10)
    city = st.sidebar.text_input("Or enter City:")
    state = st.sidebar.text_input("State:")
    radius = st.sidebar.slider("Search Radius (miles)", min_value=1, max_value=100, value=40)

    # Determine candidate coordinates
    candidate_latlon = None
    if zip_code:
        candidate_latlon = geocode_location(zip_code)
    if not candidate_latlon and city and state:
        candidate_latlon = geocode_location(f"{city}, {state}")

    if candidate_latlon is None:
        st.error("Invalid or missing candidate location. Please provide a valid ZIP code or City and State.")
        st.stop()

    # Geocode job locations
    df_expanded['Job_LatLon'] = df_expanded['Location'].apply(lambda x: geocode_location(x))
    df_expanded = df_expanded.dropna(subset=['Job_LatLon']).reset_index(drop=True)

    # Compute distance
    df_expanded['Distance'] = df_expanded['Job_LatLon'].apply(lambda loc: compute_distance(candidate_latlon, loc))

    # Filter by radius
    df_filtered = df_expanded[df_expanded['Distance'] <= radius].sort_values(by='Distance').reset_index(drop=True)

    if df_filtered.empty:
        st.warning(f"No jobs found within {radius} miles of your location.")
    else:
        st.markdown(f"### Jobs within {radius} miles:")

        # Display job cards with expandable details
        for idx, row in df_filtered.iterrows():
            with st.expander(f"{row.get('Client','')} - {row.get('Job_Title','')} - {row.get('Location','')} ({row['Distance']:.1f} mi)"):
                details_str = ""
                for col in df_filtered.columns:
                    if col not in ['Job_LatLon', 'Distance']:
                        details_str += f"{col}: {row.get(col,'')}\n"
                st.text(details_str)
else:
    st.info("Please upload a CSV file with job listings to start searching.")
