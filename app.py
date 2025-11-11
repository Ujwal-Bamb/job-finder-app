import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import ast
import re

# Initialize geolocator
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

@st.cache_data(show_spinner=False)
def batch_geocode_locations(locations):
    results = []
    for loc in locations:
        results.append(geocode_location(loc))
    return results

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
            loc_list = ast.literal_eval(loc_str)
            if isinstance(loc_list, list):
                return [x.strip() for x in loc_list if x.strip()]
        except:
            pass
    for sep in ['|', ';']:
        if sep in loc_str:
            return [x.strip() for x in loc_str.split(sep) if x.strip()]
    return [loc_str]

# ------------------- Blue-Green Glassmorphic Styles -------------------
WELCOME_STYLE = '''
<style>
body,html,#root {height:100%; margin:0; font-family:sans-serif; overflow:hidden;}
.full-page {
    min-height:100vh; width:100vw; display:flex; flex-direction:column; justify-content:center; align-items:center;
    background: linear-gradient(-45deg, #40e0d0, #1e90ff, #aeeeee, #00bfff);
    background-size:400% 400%;
    animation: gradientBG 18s ease infinite;
}
@keyframes gradientBG {0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}
.title {
    font-size:3rem;
    font-weight:700;
    color:#fff;
    text-align:center;
    margin-bottom:1rem;
    background: rgba(0, 150, 255, 0.12);
    backdrop-filter: blur(3px);
    border-radius:20px;
    padding:0.6rem 2rem;
    box-shadow:0 2px 20px #23ecb7, 0 0 10px #fff8;
}
.subtitle {
    font-size:1.45rem;
    color:#f8faff;
    text-align:center;
    margin-bottom:2.2rem;
    background: rgba(20, 230, 200, 0.15);
    backdrop-filter: blur(2.5px);
    border-radius:12px;
    padding:0.5rem 1.3rem;
    box-shadow:0 2px 18px #92e3d6, 0 0 6px #fff6;
}
.pulse-button {
    display:inline-block;
    font-size:1.4rem;
    font-weight:600;
    border-radius:40px;
    background: linear-gradient(90deg,#23ecb7,#1e90ff,#40e0d0 95%);
    color:white;
    padding:0.7rem 2.6rem;
    box-shadow:0 0 24px #23ecb799;
    border:none;
    cursor:pointer;
    animation:pulse 2.2s infinite;
    transition: background 0.2s, transform 0.2s;
    margin-top:2rem;
    letter-spacing: 1.1px;
    filter: drop-shadow(0 0 8px #40e0d088);
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
    background: rgba(255,255,255,0.12);
    border-radius: 18px;
    padding: 15px;
    margin: 12px 0;
    color: #034969;
    cursor: pointer;
    box-shadow: 0 8px 18px #23ecb744, 0 0 0 #fff4;
    transition: transform 0.3s, box-shadow 0.3s;
    border: 1px solid #45d6e7;
    backdrop-filter: blur(8px);
}
.job-card:hover {
    transform: translateY(-6px) scale(1.015);
    box-shadow: 0 16px 32px #23ecb799, 0 0 0 #fff6;
    border-color: #187cff;
}
.job-title {
    font-size: 1.37rem;
    font-weight: 700;
    color: #007bff;
}
.job-location {
    font-size: 1.06rem;
    color: #40e0d0;
    font-style: italic;
}
.job-distance {
    font-size: 1.06rem;
    color: #23ecb7;
    font-weight: 600;
}
.details {
    margin-top: 0.7rem;
    font-size: 1rem;
    color: #025262;
    white-space: pre-line;
}
.st-expander > div:first-child {
    background-color: rgba(255,255,255,0.22) !important;
    border-radius: 13px;
    color: #012f3a;
}
.st-expander > div:first-child:hover {
    background-color: #aeeeee30 !important;
}
</style>
'''

def show_welcome():
    st.markdown(WELCOME_STYLE, unsafe_allow_html=True)
    st.markdown("""
    <div class='full-page'>
      <div class='title'>😊 Keep Smiling Job Finder</div>
      <div class='subtitle'>Find your next opportunity closer to home 💼</div>
      <form action='#'>
        <button class='pulse-button' disabled>Let's Start</button>
      </form>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; margin-top:-85px;'>", unsafe_allow_html=True)
    if st.button("Let's Start"):
        st.session_state.welcome_done = True
    st.markdown("</div>", unsafe_allow_html=True)

def main_page():
    st.markdown(JOB_CARD_STYLE, unsafe_allow_html=True)
    st.title("Keep Smiling Job Finder")

    uploaded_file = st.file_uploader("Upload your jobs CSV", type=["csv"])
    if not uploaded_file:
        st.info("Please upload a CSV file with job listings to start searching.")
        return

    df = pd.read_csv(uploaded_file)
    expanded_rows = []
    for _, row in df.iterrows():
        locations = parse_locations(row.get('Location', ''))
        for loc in locations:
            new_row = row.copy()
            new_row['Location'] = loc
            expanded_rows.append(new_row)
    df_expanded = pd.DataFrame(expanded_rows)

    st.sidebar.header("Candidate Location")
    zip_code = st.sidebar.text_input("ZIP code (5-digit)")
    city = st.sidebar.text_input("City")
    state = st.sidebar.text_input("State (2-letter abbreviation)").upper()
    radius = st.sidebar.slider("Search Radius (miles)", 1, 100, 40)

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

    cache_key = f"jobs_hash_{hash(pd.util.hash_pandas_object(df_expanded).sum())}"
    if cache_key not in st.session_state:
        locs = df_expanded['Location'].fillna('').tolist()
        coords = batch_geocode_locations(locs)
        st.session_state[cache_key] = coords
    else:
        coords = st.session_state[cache_key]

    df_expanded['Job_LatLon'] = coords
    df_expanded = df_expanded.dropna(subset=['Job_LatLon']).reset_index(drop=True)
    df_expanded['Distance'] = df_expanded['Job_LatLon'].apply(lambda loc: compute_distance(candidate_latlon, loc))
    df_filtered = df_expanded[df_expanded['Distance'] <= radius].sort_values(by='Distance')

    st.markdown(f"### Jobs found within {radius} miles: {len(df_filtered)}")
    if df_filtered.empty:
        st.warning(f"No jobs found within {radius} miles.")
        return

    for idx, row in df_filtered.iterrows():
        with st.expander(f"{row.get('Client', '')} - {row.get('Job_Title', '')} ({row.get('Location', '')}) - {row['Distance']:.1f} mi"):
            details = ""
            for col in df_filtered.columns:
                if col not in ['Job_LatLon', 'Distance']:
                    details += f"{col}: {row.get(col, '')}\n"
            st.text(details)

st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
if 'welcome_done' not in st.session_state:
    st.session_state.welcome_done = False

if not st.session_state.welcome_done:
    show_welcome()
else:
    main_page()
