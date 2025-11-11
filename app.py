import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
st.title("😊 Keep Smiling Job Finder")
st.write("Find your next job closer to home 💼")

# ------------------ Load California Cities from GitHub ----------------
@st.cache_data
def load_ca_cities_github(url):
    """Load California cities CSV from GitHub and return dict city -> (lat, lon)."""
    df = pd.read_csv(url)
    city_dict = {}
    for _, row in df.iterrows():
        city_name = row['city'].strip().title()
        lat, lon = row['lat'], row['lng']
        city_dict[city_name] = (lat, lon)
    return city_dict

GITHUB_URL = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/refs/heads/main/california_cities_minimal.csv"
CA_CITIES = load_ca_cities_github(GITHUB_URL)

# ------------------ Helper Functions ----------------
def parse_job_locations(loc_str):
    if pd.isna(loc_str):
        return []
    return [x.strip().title() for x in str(loc_str).split(',') if x.strip()]

def expand_jobs(df, col='location'):
    rows = []
    for _, row in df.iterrows():
        cities = parse_job_locations(row[col])
        for city in cities:
            new_row = row.copy()
            new_row[col] = city
            rows.append(new_row)
    return pd.DataFrame(rows).reset_index(drop=True)

def distance_miles(coord1, coord2):
    return geodesic(coord1, coord2).miles

# ------------------ Upload Job CSV ----------------
uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)
    jobs_df = expand_jobs(jobs_df, 'location')  # Expand multi-city jobs

    # ------------------ Candidate Input ----------------
    st.sidebar.header("Candidate Location")
    candidate_city = st.sidebar.text_input("Enter your city (California)").strip().title()
    search_radius = st.sidebar.slider("Search radius (miles)", 1, 100, 50)
    search_btn = st.sidebar.button("Find Jobs")

    if search_btn:
        if candidate_city not in CA_CITIES:
            st.error("Invalid city! Please enter a valid California city from CSV.")
        else:
            candidate_coord = CA_CITIES[candidate_city]

            # Map job locations to coordinates
            jobs_df['Job_Coords'] = jobs_df['location'].apply(lambda x: CA_CITIES.get(x))
            jobs_df = jobs_df.dropna(subset=['Job_Coords']).reset_index(drop=True)

            # Compute distances
            jobs_df['Distance'] = jobs_df['Job_Coords'].apply(lambda x: distance_miles(candidate_coord, x))

            # Filter by radius
            filtered_jobs = jobs_df[jobs_df['Distance'] <= search_radius].sort_values('Distance').reset_index(drop=True)

            if filtered_jobs.empty:
                st.warning(f"No jobs found within {search_radius} miles of {candidate_city}.")
            else:
                st.subheader(f"Jobs within {search_radius} miles of {candidate_city}:")
                for _, row in filtered_jobs.iterrows():
                    with st.expander(f"{row['client_name']} - {row['job_title']} ({row['location']}) — {row['Distance']:.1f} mi"):
                        for col in filtered_jobs.columns:
                            if col not in ['Job_Coords', 'Distance']:
                                st.write(f"**{col}:** {row[col]}")

                # Map
                map_data = pd.DataFrame(filtered_jobs['Job_Coords'].tolist(), columns=['lat', 'lon'])
                map_data['job_title'] = filtered_jobs['job_title']
                st.map(map_data)
else:
    st.info("Upload a CSV file with job listings to start searching.")
