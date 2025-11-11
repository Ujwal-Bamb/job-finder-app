import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# ------------------ Streamlit setup ------------------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
st.title("😊 Keep Smiling Job Finder")
st.markdown("Find your next job closer to home 💼")

# ------------------ Load California cities + ZIPs ------------------
@st.cache_data(show_spinner=False)
def load_ca_cities_github(url):
    df = pd.read_csv(url)
    city_dict = {}
    zip_dict = {}
    for _, row in df.iterrows():
        city_name = str(row['city']).strip().title()
        lat, lng = row['lat'], row['lng']
        city_dict[city_name] = (lat, lng)
        if pd.notna(row['zips']):
            for z in str(row['zips']).split():
                zip_dict[z] = (lat, lng)
    return city_dict, zip_dict

GITHUB_URL = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/refs/heads/main/california_cities_minimal.csv"
CA_CITIES, ZIP_TO_COORD = load_ca_cities_github(GITHUB_URL)
CITY_LIST = sorted(CA_CITIES.keys())

# ------------------ Helper functions ------------------
def normalize_location(loc):
    if isinstance(loc, str):
        return loc.strip().title()
    return loc

def haversine_miles(coord1, coord2):
    """Fast distance calculator in miles"""
    R = 3958.8  # Earth radius in miles
    lat1, lon1 = map(radians, coord1)
    lat2, lon2 = map(radians, coord2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def fuzzy_city_lookup(city_name):
    """Try to match a possibly misspelled or extended city name"""
    if not isinstance(city_name, str) or not city_name.strip():
        return None
    city_name = normalize_location(city_name.split(",")[0])  # remove ', CA' or similar
    if city_name in CA_CITIES:
        return CA_CITIES[city_name]
    match = get_close_matches(city_name, CITY_LIST, n=1, cutoff=0.8)
    if match:
        return CA_CITIES[match[0]]
    return None

# ------------------ Upload Jobs CSV ------------------
uploaded_file = st.file_uploader("📂 Upload your jobs CSV file", type=['csv'])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)
    if 'location' not in jobs_df.columns:
        st.error("Your CSV must include a 'location' column for job city names.")
        st.stop()

    # Normalize job locations
    jobs_df['location'] = jobs_df['location'].apply(normalize_location)

    # Sidebar Inputs
    st.sidebar.header("Search Jobs")
    search_type = st.sidebar.radio("Search by:", ["City", "ZIP Code"])

    candidate_coord = None
    candidate_city = None
    candidate_zip = None

    if search_type == "City":
        typed = st.sidebar.text_input("Enter your city (California)").strip().title()
        suggestions = []
        if typed and len(typed) >= 2:
            suggestions = [c for c in CITY_LIST if typed in c]
            if suggestions:
                candidate_city = st.sidebar.selectbox("Select a city:", suggestions)
            else:
                st.sidebar.info("No matching city found. Try another input.")
        else:
            st.sidebar.info("Please type at least 2 characters for city suggestions.")
    else:
        zip_input = st.sidebar.text_input("Enter ZIP code (5 digits)").strip()
        if zip_input:
            if zip_input.isdigit() and len(zip_input) == 5:
                if zip_input in ZIP_TO_COORD:
                    candidate_zip = zip_input
                else:
                    st.sidebar.error("ZIP code not found in California database.")
            else:
                st.sidebar.error("Invalid ZIP code. Please enter 5 digits.")

    search_radius = st.sidebar.slider("Search radius (miles)", 1, 100, 50)
    search_btn = st.sidebar.button("🔍 Find Jobs")

    if search_btn:
        # Determine candidate coordinates
        if search_type == "City":
            if not candidate_city or candidate_city not in CA_CITIES:
                st.error("Please select a valid California city from suggestions.")
                st.stop()
            candidate_coord = CA_CITIES[candidate_city]
        else:
            if not candidate_zip or candidate_zip not in ZIP_TO_COORD:
                st.error("ZIP code not found in California ZIPs database.")
                st.stop()
            candidate_coord = ZIP_TO_COORD[candidate_zip]

        # ✅ FIXED INDENTATION BLOCK
        with st.spinner("Finding nearby jobs..."):
            # Map job locations to coordinates using fuzzy matching
            jobs_df['Job_Coords'] = jobs_df['location'].apply(fuzzy_city_lookup)

            # Inform user if any jobs missing valid city mapping
            missing_coords_jobs = jobs_df[jobs_df['Job_Coords'].isna()]
            if not missing_coords_jobs.empty:
                st.warning(f"{len(missing_coords_jobs)} job(s) were ignored due to unrecognized city names.")

            # Drop jobs with unknown coordinates
            jobs_df = jobs_df.dropna(subset=['Job_Coords']).reset_index(drop=True)

            # Compute distances
            jobs_df['Distance'] = jobs_df['Job_Coords'].apply(lambda x: haversine_miles(candidate_coord, x))

            # Filter by radius
            filtered_jobs = jobs_df[jobs_df['Distance'] <= search_radius].sort_values('Distance').reset_index(drop=True)

        # ✅ Everything below runs after the 'with' block
        if filtered_jobs.empty:
            st.warning(f"No jobs found within {search_radius} miles of your location.")
        else:
            st.success(f"🎯 Found {len(filtered_jobs)} job(s) within {search_radius} miles!")

            # Show summary stats
            st.metric("Closest Job (miles)", f"{filtered_jobs['Distance'].min():.1f}")
            st.metric("Farthest Job (miles)", f"{filtered_jobs['Distance'].max():.1f}")

            # Display jobs
            for _, row in filtered_jobs.iterrows():
                schedule = row.get('schedule', '')
                language = row.get('language', '')
                gender = row.get('gender', '')

                # Clean field strings
                schedule_str = f"Schedule: {schedule}" if schedule else ""
                language_str = f"Language: {language}" if language else ""
                gender_str = f"Gender: {gender}" if gender else ""

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #6a11cb, #2575fc);
                            border-radius:12px; padding:15px; margin:10px 0; color:white;">
                    <b>{row.get('client_name', 'Unknown Client')} - {row.get('job_title', 'Job')}</b><br>
                    {row['location']} — {row['Distance']:.1f} mi<br>
                    {schedule_str}<br>
                    {language_str}<br>
                    {gender_str}
                </div>
                """, unsafe_allow_html=True)

            # Map plot
            map_data = pd.DataFrame(filtered_jobs['Job_Coords'].tolist(), columns=['lat', 'lon'])
            map_data['job_title'] = filtered_jobs.get('job_title', '')
            st.map(map_data)

else:
    st.info("📄 Upload a CSV file with job listings to start searching.")
