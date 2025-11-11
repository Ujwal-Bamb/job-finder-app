import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import ast
import re

# Initialize geolocator
geolocator = Nominatim(user_agent="keep_smiling_job_finder")

# ------------------- Caching -------------------
@st.cache_data(show_spinner=False)
def geocode_location(location_str):
    """Return latitude and longitude for a location string"""
    try:
        loc = geolocator.geocode(location_str)
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None

@st.cache_data(show_spinner=False)
def batch_geocode_locations(locations):
    results = []
    for loc in locations:
        results.append(geocode_location(loc))
    return results

# ------------------- Distance Calculation -------------------
def compute_distance(loc1, loc2):
    try:
        return geodesic(loc1, loc2).miles
    except:
        return np.inf

# ------------------- Multi-location Parser -------------------
def parse_locations(loc_str):
    if pd.isna(loc_str):
        return []
    loc_str = str(loc_str).strip()
    # Handle list-style formats
    if loc_str.startswith('[') and loc_str.endswith(']'):
        try:
            loc_list = ast.literal_eval(loc_str)
            if isinstance(loc_list, list):
                return [x.strip() for x in loc_list if x.strip()]
        except:
            pass
    # Split by | or ; for safe parsing
    for sep in ['|', ';']:
        if sep in loc_str:
            return [x.strip() for x in loc_str.split(sep) if x.strip()]
    # Treat whole as single location otherwise
    return [loc_str]

# ------------------- CSS Styles -------------------
WELCOME_STYLE = '''
<style>
body,html,#root {height:100%; margin:0; font-family:sans-serif; overflow:hidden;}
.full-page {
    min-height:100vh; width:100vw; display:flex; flex-direction:column; justify-content:center; align-items:center;
    background: linear-gradient(-45deg, #ff6b6b, #556270, #c7f464, #ff6b6b);
    background-size:400% 400%;
    animation: gradientBG 15s ease infinite;
}
@keyframes gradientBG {0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}
.title {
    font-size:3rem;
    font-weight:700;
    color:white;
    text-shadow:0 0 14px #ab47bc;
    margin-bottom:1rem;
    text-align:center;
    animation:glow 3s ease-in-out infinite alternate;
}
@keyframes glow {
    from { text-shadow: 0 0 10px #bb33ff; }
    to { text-shadow: 0 0 30px #ff33ff; }
}
.subtitle {
    font-size:1.5rem;
    color:#ffefde;
    text-align:center;
    margin-bottom:2.5rem;
}
.pulse-button {
    display:inline-block;
    font-size:1.5rem;
    font-weight:600;
    border-radius:35px;
    background:linear-gradient(90deg,#21d4fd 0%,#b721ff 100%);
    color:white;
    padding:0.7rem 2.8rem;
    box-shadow:0 0 15px rgba(183,33,255,0.6);
    border:none;
    cursor:pointer;
    animation:pulse 2.2s infinite;
    transition: background 0.2s, transform 0.2s;
    margin-top:2rem;
}
@keyframes pulse {
    0% {transform:scale(1);}
    50% {transform:scale(1.07);}
    100% {transform:scale(1);}
}
</style>
'''

JOB_CARD_STYLE = '''
<style>
.job-card {
    background: #1e1e2f;
    border-radius: 15px;
    padding: 15px;
    margin: 10px 0;
    color: white;
    cursor: pointer;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    border: 1px solid #333;
}
.job-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(110, 84, 247, 0.5);
    border-color: #6e54f7;
}
.job-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #9a7dff;
}
.job-location {
    font-size: 1rem;
    color: #ccc;
    font-style: italic;
}
.job-distance {
    font-size: 0.9rem;
    color: #82e8a2;
    font-weight: 600;
}
.details {
    margin-top: 0.8rem;
    font-size: 0.9rem;
    color: #ddd;
    white-space: pre-line;
}
.st-expander > div:first-child {
    background-color: #272727 !important;
    border-radius: 12px;
    color: white;
}
.st-expander > div:first-child:hover {
    background-color: #3a3a3a !important;
}
</style>
'''

# ------------------- Welcome Page -------------------
def show_welcome():
    st.markdown(WELCOME_STYLE, unsafe_allow_html=True)
    st.markdown("""
    <div class='full-page'>
      <div class='title'>😊 Keep Smiling Job Finder</div>
      <div class='subtitle'>Find your next opportunity closer to home 💼</div>
      <form action='#'>
        <!-- Just visual: The Streamlit button is below -->
        <button class='pulse-button' disabled>Let's Start</button>
      </form>
    </div>
    """, unsafe_allow_html=True)
    # Streamlit button for state tracking, placed below styled area
    # Visually only the animated button is seen, but this triggers the session flag
    st.markdown("<div style='text-align:center; margin-top:-90px;'>", unsafe_allow_html=True)
    if st.button("Let's Start"):
        st.session_state.welcome_done = True
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------- Main Page -------------------
def main_page():
    st.markdown(JOB_CARD_STYLE, unsafe_allow_html=True)
    st.title("Keep Smiling Job Finder")

    uploaded_file = st.file_uploader("Upload your jobs CSV", type=["csv"])
    if not uploaded_file:
        st.info("Please upload a CSV file with job listings to start searching.")
        return

    df = pd.read_csv(uploaded_file)

    # Expand multi-location jobs
    expanded_rows = []
    for _, row in df.iterrows():
        locations = parse_locations(row.get('Location', ''))
        for loc in locations:
            new_row = row.copy()
            new_row['Location'] = loc
            expanded_rows.append(new_row)
    df_expanded = pd.DataFrame(expanded_rows)

    # Candidate input (sidebar)
    st.sidebar.header("Candidate Location")
    zip_code = st.sidebar.text_input("ZIP code (5-digit)")
    city = st.sidebar.text_input("City")
    state = st.sidebar.text_input("State (2-letter abbreviation)").upper()
    radius = st.sidebar.slider("Search Radius (miles)", 1, 100, 40)

    # Validate candidate input
    candidate_latlon = None
    valid_input = True
    error_msg = ""

    if zip_code and re.fullmatch(r'\d{5}', zip_code):
        candidate_latlon = geocode_location(zip_code)
        if candidate_latlon is None:
            valid_input = False
            error_msg = "ZIP code not found."
    elif city and state and re.fullmatch(r'[A-Z]{2}', state):
        candidate_latlon = geocode_location(f"{city}, {state}, USA")
        if candidate_latlon is None:
            valid_input = False
            error_msg = "City and State combination not found."
    else:
        valid_input = False
        error_msg = "Please enter a valid 5-digit ZIP code or City + 2-letter State."

    if not valid_input:
        st.sidebar.error(error_msg)
        return

    # Pre-geocode job locations (cached by upload hash)
    cache_key = f"jobs_hash_{hash(pd.util.hash_pandas_object(df_expanded).sum())}"
    if cache_key not in st.session_state:
        locs = df_expanded['Location'].fillna('').tolist()
        coords = batch_geocode_locations(locs)
        st.session_state[cache_key] = coords
    else:
        coords = st.session_state[cache_key]

    df_expanded['Job_LatLon'] = coords

    # Drop jobs with invalid location
    df_expanded = df_expanded.dropna(subset=['Job_LatLon']).reset_index(drop=True)

    # Compute distances
    df_expanded['Distance'] = df_expanded['Job_LatLon'].apply(lambda loc: compute_distance(candidate_latlon, loc))

    # Filter jobs by radius
    df_filtered = df_expanded[df_expanded['Distance'] <= radius].sort_values(by='Distance')

    st.markdown(f"### Jobs found within {radius} miles: {len(df_filtered)}")

    if df_filtered.empty:
        st.warning(f"No jobs found within {radius} miles.")
        return

    # Display job cards with expandable details
    for idx, row in df_filtered.iterrows():
        with st.expander(f"{row.get('Client', '')} - {row.get('Job_Title', '')} ({row.get('Location', '')}) - {row['Distance']:.1f} mi"):
            details = ""
            for col in df_filtered.columns:
                if col not in ['Job_LatLon', 'Distance']:
                    details += f"{col}: {row.get(col, '')}\n"
            st.text(details)


# ------------------- Session Handling -------------------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
if 'welcome_done' not in st.session_state:
    st.session_state.welcome_done = False

if not st.session_state.welcome_done:
    show_welcome()
else:
    main_page()
