import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
st.title("😊 Keep Smiling Job Finder")
st.markdown("Find your next job closer to home 💼")

# ------------------ Load California cities + coordinates ------------------
@st.cache_data
def load_ca_cities_github(url):
    df = pd.read_csv(url)
    city_dict = {}
    for _, row in df.iterrows():
        if pd.notna(row['city']) and pd.notna(row['lat']) and pd.notna(row['lng']):
            city_name = row['city'].strip().title()
            lat, lng = row['lat'], row['lng']
            city_dict[city_name] = (lat, lng)
    return city_dict

GITHUB_URL = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/refs/heads/main/california_cities_minimal.csv"
CA_CITIES = load_ca_cities_github(GITHUB_URL)
CITY_LIST = sorted(CA_CITIES.keys())

# ------------------ Helper functions ------------------
def distance_miles(coord1, coord2):
    return geodesic(coord1, coord2).miles

def expand_jobs(df, col='location'):
    rows = []
    for _, row in df.iterrows():
        if pd.isna(row[col]) or not str(row[col]).strip():
            continue
        cities = [x.strip().title() for x in str(row[col]).split(',') if x.strip()]
        for city in cities:
            new_row = row.copy()
            new_row[col] = city
            rows.append(new_row)
    return pd.DataFrame(rows).reset_index(drop=True)

# ------------------ Upload Jobs CSV ------------------
uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)

    # Remove rows with missing location or client/job title
    jobs_df = jobs_df.dropna(subset=['client_name','job_title','location']).reset_index(drop=True)
    jobs_df = expand_jobs(jobs_df, 'location')

    # ------------------ Candidate Input ------------------
    st.sidebar.header("Search Jobs by City")
    typed = st.sidebar.text_input("Enter your city (California)").strip().title()
    candidate_city = None
    if typed and len(typed) >= 2:
        suggestions = [c for c in CITY_LIST if typed in c]
        if suggestions:
            candidate_city = st.sidebar.selectbox("Select a city:", suggestions)

    search_radius = st.sidebar.slider("Search radius (miles)", 1, 100, 50)
    search_btn = st.sidebar.button("Find Jobs")

    if search_btn:
        if not candidate_city or candidate_city not in CA_CITIES:
            st.error("Please select a valid California city from suggestions.")
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
                        st.write(f"**Client:** {row['client_name']}")
                        st.write(f"**Job Title:** {row['job_title']}")
                        st.write(f"**Location:** {row['location']}")
                        if 'schedule' in row and pd.notna(row['schedule']):
                            st.write(f"**Schedule:** {row['schedule']}")
                        if 'language' in row and pd.notna(row['language']):
                            st.write(f"**Language:** {row['language']}")
                        if 'gender' in row and pd.notna(row['gender']):
                            st.write(f"**Gender:** {row['gender']}")

                # Map
                map_data = pd.DataFrame(filtered_jobs['Job_Coords'].tolist(), columns=['lat','lon'])
                map_data['job_title'] = filtered_jobs['job_title']
                st.map(map_data)
else:
    st.info("Upload a CSV file with job listings to start searching.")
