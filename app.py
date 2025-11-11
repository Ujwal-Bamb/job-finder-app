import streamlit as st
import pandas as pd
import numpy as np
import ast
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# ------------------ Initialization ------------------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")

if 'page' not in st.session_state:
    st.session_state.page = 'welcome'

# ------------------ Geocoding ------------------
@st.cache_data(show_spinner=False)
def geocode_location(location_str):
    geolocator = Nominatim(user_agent="keep_smiling_job_finder_app")
    try:
        loc = geolocator.geocode(f"{str(location_str).strip()}, USA", timeout=10)
        if loc:
            return (loc.latitude, loc.longitude)
    except (GeocoderTimedOut, GeocoderServiceError):
        return None
    except Exception:
        return None
    return None

# ------------------ Distance ------------------
def compute_distance(loc1, loc2):
    try:
        return geodesic(loc1, loc2).miles
    except:
        return np.inf

# ------------------ Multi-location Parsing ------------------
def parse_locations(loc_str):
    if pd.isna(loc_str):
        return []
    loc_str = str(loc_str).strip()
    if loc_str.startswith('[') and loc_str.endswith(']'):
        try:
            loc_list = ast.literal_eval(loc_str)
            if isinstance(loc_list, list):
                return [x.strip() for x in loc_list if str(x).strip()]
        except:
            pass
    for sep in [',', '/', '|', ';']:
        if sep in loc_str:
            return [x.strip() for x in loc_str.split(sep) if x.strip()]
    return [loc_str]

def expand_multi_locations(df, col='Location'):
    if col not in df.columns:
        st.error(f"Missing '{col}' column in CSV.")
        return df
    rows = []
    for _, row in df.iterrows():
        locs = parse_locations(row.get(col, ''))
        if not locs:
            rows.append(row)
        else:
            for loc in locs:
                new_row = row.copy()
                new_row[col] = loc
                rows.append(new_row)
    return pd.DataFrame(rows).reset_index(drop=True)

# ------------------ Welcome Page ------------------
def show_welcome_page():
    st.markdown("<h1 style='text-align:center; margin-top:150px;'>😊 Keep Smiling Job Finder</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Find your next job closer to home 💼</p>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; margin-top:50px;'>", unsafe_allow_html=True)
    if st.button("🚀 Let's Get Started", key='start_btn'):
        st.session_state.page = 'main'
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ Main Page ------------------
def show_main_page():
    st.header("Job Search")

    uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])
    if uploaded_file is None:
        st.info("Please upload a CSV file to start searching for jobs.")
        return

    df = pd.read_csv(uploaded_file)
    df = expand_multi_locations(df, 'Location')

    # Candidate Inputs
    st.sidebar.header("Candidate Location")
    zip_code = st.sidebar.text_input("ZIP Code")
    city = st.sidebar.text_input("City")
    state = st.sidebar.text_input("State (2-letter code)")
    radius = st.sidebar.slider("Search Radius (miles)", 1, 100, 50)
    search_btn = st.sidebar.button("Find Jobs")

    if not search_btn:
        st.info("Enter your location and click **Find Jobs** to search.")
        return

    # Geocode candidate
    candidate_loc = None
    if zip_code:
        candidate_loc = geocode_location(zip_code)
    if not candidate_loc and city and state:
        candidate_loc = geocode_location(f"{city}, {state}")
    if not candidate_loc:
        st.error("Invalid location! Please enter a valid ZIP or City + State.")
        return

    # Geocode job locations
    st.write("📍 Geocoding job locations, please wait...")
    df['Job_LatLon'] = df['Location'].apply(lambda x: geocode_location(x))
    df = df.dropna(subset=['Job_LatLon']).reset_index(drop=True)

    if df.empty:
        st.warning("No valid job locations found after geocoding.")
        return

    # Compute distances
    df['Distance'] = df['Job_LatLon'].apply(lambda loc: compute_distance(candidate_loc, loc))
    df_filtered = df[df['Distance'] <= radius].sort_values('Distance').reset_index(drop=True)

    if df_filtered.empty:
        st.warning(f"No jobs found within {radius} miles.")
        return

    st.subheader(f"✅ Jobs within {radius} miles:")
    for _, row in df_filtered.iterrows():
        with st.expander(f"{row.get('Client','')} - {row.get('Job_Title','')} ({row['Location']}) — {row['Distance']:.1f} mi"):
            details = ""
            for col in df_filtered.columns:
                if col not in ['Job_LatLon', 'Distance']:
                    details += f"{col}: {row.get(col,'')}\n"
            st.text(details)

    # Map visualization
    map_data = pd.DataFrame([{'lat': loc[0], 'lon': loc[1]} for loc in df_filtered['Job_LatLon']])
    st.map(map_data)

# ------------------ Page Navigation ------------------
if st.session_state.page == 'welcome':
    show_welcome_page()
else:
    show_main_page()
