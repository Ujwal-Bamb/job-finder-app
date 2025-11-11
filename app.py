import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
st.title("😊 Keep Smiling Job Finder")
st.markdown("Find your next job closer to home 💼")

# ------------------ Load California cities + ZIPs ------------------
@st.cache_data
def load_ca_cities_github(url):
    df = pd.read_csv(url)
    city_dict = {}
    zip_dict = {}
    for _, row in df.iterrows():
        city_name = row['city'].strip().title()
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
def distance_miles(coord1, coord2):
    return geodesic(coord1, coord2).miles

# ------------------ Upload Jobs CSV ------------------
uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)
    jobs_df['location'] = jobs_df['location'].str.title()  # Normalize

    # ------------------ Candidate Input ------------------
    st.sidebar.header("Search Jobs")
    search_type = st.sidebar.radio("Search by:", ["City", "ZIP Code"])

    candidate_coord = None
    if search_type == "City":
        typed = st.sidebar.text_input("Enter your city (California)").strip().title()
        if typed and len(typed) >= 2:
            suggestions = [c for c in CITY_LIST if typed in c]
            candidate_city = st.sidebar.selectbox("Select a city:", suggestions)
        else:
            candidate_city = None
    else:
        zip_input = st.sidebar.text_input("Enter ZIP code (5 digits)").strip()
        if zip_input and zip_input.isdigit() and len(zip_input) == 5:
            candidate_zip = zip_input
        else:
            candidate_zip = None

    search_radius = st.sidebar.slider("Search radius (miles)", 1, 100, 50)
    search_btn = st.sidebar.button("Find Jobs")

    if search_btn:
        # Validate input
        if search_type == "City":
            if not candidate_city or candidate_city not in CA_CITIES:
                st.error("Please select a valid California city from suggestions.")
            else:
                candidate_coord = CA_CITIES[candidate_city]
        else:
            if not candidate_zip or candidate_zip not in ZIP_TO_COORD:
                st.error("ZIP code not found in California ZIPs database.")
            else:
                candidate_coord = ZIP_TO_COORD[candidate_zip]

        if candidate_coord:
            # Map job locations to coordinates
            jobs_df['Job_Coords'] = jobs_df['location'].apply(lambda x: CA_CITIES.get(x))
            jobs_df = jobs_df.dropna(subset=['Job_Coords']).reset_index(drop=True)

            # Compute distances
            jobs_df['Distance'] = jobs_df['Job_Coords'].apply(lambda x: distance_miles(candidate_coord, x))

            # Filter by radius
            filtered_jobs = jobs_df[jobs_df['Distance'] <= search_radius].sort_values('Distance').reset_index(drop=True)

            if filtered_jobs.empty:
                st.warning(f"No jobs found within {search_radius} miles of your location.")
            else:
                st.subheader(f"Jobs within {search_radius} miles:")
                for _, row in filtered_jobs.iterrows():
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #6a11cb, #2575fc);
                                border-radius:12px; padding:15px; margin:10px 0; color:white;">
                        <b>{row['client_name']} - {row['job_title']}</b><br>
                        {row['location']} — {row['Distance']:.1f} mi<br>
                        Schedule: {row.get('schedule','')}<br>
                        Language: {row.get('language','')}<br>
                        Gender: {row.get('gender','')}
                    </div>
                    """, unsafe_allow_html=True)

                # Map
                map_data = pd.DataFrame(filtered_jobs['Job_Coords'].tolist(), columns=['lat','lon'])
                map_data['job_title'] = filtered_jobs['job_title']
                st.map(map_data)
else:
    st.info("Upload a CSV file with job listings to start searching.")
