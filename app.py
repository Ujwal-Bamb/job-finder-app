import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# ------------------ Streamlit Page Config ------------------
st.set_page_config(
    page_title="😊 Keep Smiling Job Finder",
    layout="wide",
    page_icon="💼"
)

# ------------------ Custom CSS Styling ------------------
st.markdown("""
    <style>
    /* Background gradient */
    .stApp {
        background: linear-gradient(120deg, #f0f4ff, #e8f0ff);
        font-family: 'Segoe UI', sans-serif;
    }

    /* Title styling */
    h1 {
        text-align: center;
        color: #1e3a8a;
        margin-bottom: 0.5em;
    }

    /* Subheader */
    .subtext {
        text-align: center;
        color: #374151;
        font-size: 1.1rem;
        margin-bottom: 1.5em;
    }

    /* Job card styling */
    .job-card {
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 15px;
        border-left: 6px solid #2563eb;
        transition: transform 0.1s ease-in-out;
    }
    .job-card:hover {
        transform: scale(1.01);
    }
    .job-header {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1e3a8a;
        margin-bottom: 4px;
    }
    .job-location {
        color: #475569;
        font-size: 0.95rem;
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------ Header ------------------
st.title("😊 Keep Smiling Job Finder")
st.markdown('<p class="subtext">Find your next job closer to home 💼</p>', unsafe_allow_html=True)

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

GITHUB_URL = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/california_cities_minimal.csv"
CA_CITIES, ZIP_TO_COORD = load_ca_cities_github(GITHUB_URL)
CITY_LIST = sorted(CA_CITIES.keys())

# ------------------ Helper functions ------------------
def normalize_location(loc):
    if isinstance(loc, str):
        return loc.strip().title()
    return loc

def haversine_miles(coord1, coord2):
    R = 3958.8
    lat1, lon1 = map(radians, coord1)
    lat2, lon2 = map(radians, coord2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def fuzzy_city_lookup(city_name):
    if not isinstance(city_name, str) or not city_name.strip():
        return None
    city_name = normalize_location(city_name.split(",")[0])
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

    jobs_df['location'] = jobs_df['location'].apply(normalize_location)

    # Sidebar Inputs
    with st.sidebar:
        st.header("🔍 Search Jobs")
        search_type = st.radio("Search by:", ["City", "ZIP Code"])
        search_radius = st.slider("Search radius (miles)", 1, 100, 50)

        candidate_coord = None
        candidate_city = None
        candidate_zip = None

        if search_type == "City":
            typed = st.text_input("Enter your city (California)").strip().title()
            suggestions = []
            if typed and len(typed) >= 2:
                suggestions = [c for c in CITY_LIST if typed in c]
                if suggestions:
                    candidate_city = st.selectbox("Select a city:", suggestions)
                else:
                    st.info("No matching city found.")
            else:
                st.info("Type at least 2 characters.")
        else:
            zip_input = st.text_input("Enter ZIP code (5 digits)").strip()
            if zip_input:
                if zip_input.isdigit() and len(zip_input) == 5:
                    if zip_input in ZIP_TO_COORD:
                        candidate_zip = zip_input
                    else:
                        st.error("ZIP code not found in California.")
                else:
                    st.error("Invalid ZIP code. Must be 5 digits.")

        search_btn = st.button("🚀 Find Jobs")

    if search_btn:
        # Determine coordinates
        if search_type == "City":
            if not candidate_city or candidate_city not in CA_CITIES:
                st.error("Please select a valid California city.")
                st.stop()
            candidate_coord = CA_CITIES[candidate_city]
        else:
            if not candidate_zip or candidate_zip not in ZIP_TO_COORD:
                st.error("ZIP code not found.")
                st.stop()
            candidate_coord = ZIP_TO_COORD[candidate_zip]

        with st.spinner("🔎 Searching nearby jobs..."):
            jobs_df['Job_Coords'] = jobs_df['location'].apply(fuzzy_city_lookup)
            jobs_df = jobs_df.dropna(subset=['Job_Coords']).reset_index(drop=True)
            jobs_df['Distance'] = jobs_df['Job_Coords'].apply(lambda x: haversine_miles(candidate_coord, x))
            filtered_jobs = jobs_df[jobs_df['Distance'] <= search_radius].sort_values('Distance')

        if filtered_jobs.empty:
            st.warning(f"No jobs found within {search_radius} miles of your location.")
        else:
            st.success(f"🎯 Found {len(filtered_jobs)} job(s) within {search_radius} miles!")

            # ---- Job Cards ----
            for _, row in filtered_jobs.iterrows():
                client_name = row.get('client_name', 'Unknown Client')
                job_title = row.get('job_title', 'Job')
                location = row.get('location', 'Unknown')
                distance = row.get('Distance', 0)
                schedule = row.get('schedule', '')
                language = row.get('language', '')
                gender = row.get('gender', '')
                desc = row.get('description', '')

                with st.expander(f"💼 {client_name} - {job_title} ({location} — {distance:.1f} mi)"):
                    st.markdown(f"""
                    <div class='job-card'>
                        <div class='job-header'>{client_name} - {job_title}</div>
                        <div class='job-location'>📍 {location} — {distance:.1f} miles away</div>
                        {"<b>Schedule:</b> " + schedule if schedule else ""}
                        <br>
                        {"<b>Language:</b> " + language if language else ""}
                        <br>
                        {"<b>Gender:</b> " + gender if gender else ""}
                        <br><br>
                        {"<b>Description:</b><br>" + desc if desc else ""}
                    </div>
                    """, unsafe_allow_html=True)

            # ---- Map ----
            st.subheader("🗺️ Job Locations Map")
            map_data = pd.DataFrame(filtered_jobs['Job_Coords'].tolist(), columns=['lat', 'lon'])
            st.map(map_data)
else:
    st.info("📄 Upload a CSV file with job listings to start searching.")
