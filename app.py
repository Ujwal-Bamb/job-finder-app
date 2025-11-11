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
    .stApp {
        background: linear-gradient(135deg, #e0f2ff, #f5f7ff);
        font-family: 'Segoe UI', sans-serif;
    }
    .welcome-box {
        text-align: center;
        padding: 80px 20px;
        background: white;
        border-radius: 18px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        margin-top: 60px;
        margin-bottom: 40px;
    }
    .welcome-title {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1e3a8a;
    }
    .welcome-sub {
        font-size: 1.1rem;
        color: #475569;
        margin-top: 10px;
    }
    .section {
        background-color: white;
        padding: 20px 30px;
        border-radius: 14px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    .job-card {
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 15px;
        border-left: 6px solid #2563eb;
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
    .center-btn {
        display: flex;
        justify-content: center;
        margin-top: 40px;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------ Page State ------------------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ------------------ Welcome Page ------------------
if st.session_state.page == "welcome":
    st.markdown("""
        <div class="welcome-box">
            <div class="welcome-title">😊 Welcome to Keep Smiling Job Finder</div>
            <div class="welcome-sub">
                Find your dream job closer to home — smart, fast, and beautifully simple.<br>
                Upload your job listings, choose your location, and explore opportunities nearby!
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Use Streamlit native button (no HTML form)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Let's Start"):
            st.session_state.page = "main"
            st.rerun()

# ------------------ Main App Page ------------------
elif st.session_state.page == "main":

    st.title("😊 Keep Smiling Job Finder")
    st.markdown("### 💼 Find your next job closer to home")

    # ------------------ Load California cities + ZIPs ------------------
    @st.cache_data(show_spinner=False)
    def load_ca_cities_github(url):
        df = pd.read_csv(url)
        city_dict, zip_dict = {}, {}
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

    # ------------------ Helper Functions ------------------
    def normalize_location(loc):
        return loc.strip().title() if isinstance(loc, str) else loc

    def haversine_miles(coord1, coord2):
        R = 3958.8
        lat1, lon1 = map(radians, coord1)
        lat2, lon2 = map(radians, coord2)
        dlon, dlat = lon2 - lon1, lat2 - lat1
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

    # ------------------ Upload CSV ------------------
    st.markdown("### 📂 Upload Job Data")
    uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])

    if uploaded_file:
        jobs_df = pd.read_csv(uploaded_file)
        if 'location' not in jobs_df.columns:
            st.error("Your CSV must include a 'location' column.")
            st.stop()

        jobs_df['location'] = jobs_df['location'].apply(normalize_location)

        # ------------------ Search Form ------------------
        st.markdown("### 🔍 Search Jobs Near You")
        st.markdown('<div class="section">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            search_type = st.radio("Search by:", ["City", "ZIP Code"])
        with col2:
            search_radius = st.slider("Search radius (miles)", 1, 100, 50)

        candidate_coord = None

        if search_type == "City":
            city_input = st.text_input("Enter your city (California)").strip().title()
            if city_input and len(city_input) >= 2:
                suggestions = [c for c in CITY_LIST if city_input in c]
                if suggestions:
                    candidate_city = st.selectbox("Select city:", suggestions)
                else:
                    st.info("No matching city found.")
            else:
                st.info("Type at least 2 characters.")
        else:
            zip_input = st.text_input("Enter ZIP code (5 digits)").strip()
            if zip_input:
                if zip_input in ZIP_TO_COORD:
                    candidate_coord = ZIP_TO_COORD[zip_input]
                else:
                    st.error("ZIP not found in California.")

        st.markdown('<div class="center-btn">', unsafe_allow_html=True)
        search_btn = st.button("🔍 Find Jobs")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ------------------ Search Results ------------------
        if search_btn:
            if search_type == "City":
                if not city_input:
                    st.error("Please enter a valid city.")
                    st.stop()
                candidate_coord = CA_CITIES.get(city_input) or fuzzy_city_lookup(city_input)

            if not candidate_coord:
                st.error("Unable to determine your location.")
                st.stop()

            with st.spinner("🔎 Searching nearby jobs..."):
                jobs_df['Job_Coords'] = jobs_df['location'].apply(fuzzy_city_lookup)
                jobs_df = jobs_df.dropna(subset=['Job_Coords']).reset_index(drop=True)
                jobs_df['Distance'] = jobs_df['Job_Coords'].apply(lambda x: haversine_miles(candidate_coord, x))
                filtered_jobs = jobs_df[jobs_df['Distance'] <= search_radius].sort_values('Distance')

            if filtered_jobs.empty:
                st.warning(f"No jobs found within {search_radius} miles.")
            else:
                st.success(f"🎯 Found {len(filtered_jobs)} job(s) nearby!")
                for _, row in filtered_jobs.iterrows():
                    client_name = row.get('client_name', 'Unknown Client')
                    job_title = row.get('job_title', 'Job')
                    location = row.get('location', 'Unknown')
                    distance = row.get('Distance', 0)
                    schedule = row.get('schedule', '')
                    language = row.get('language', '')
                    gender = row.get('gender', '')
                    desc = row.get('description', '')

                    with st.expander(f"💼 {client_name} - {job_title} ({distance:.1f} mi)"):
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
