import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
st.title("😊 Keep Smiling Job Finder")
st.markdown("Find your next job closer to home 💼")

# ------------------ Load California cities with ZIPs ------------------
@st.cache_data
def load_ca_cities_github(url):
    df = pd.read_csv(url)
    city_dict = {}
    zip_dict = {}
    for _, row in df.iterrows():
        city_name = row['city'].strip().title()
        lat, lng = row['lat'], row['lng']
        city_dict[city_name] = (lat, lng)
        # expand multiple ZIPs
        if pd.notna(row['zips']):
            for z in str(row['zips']).split():
                zip_dict[z] = (lat, lng)
    return city_dict, zip_dict

GITHUB_URL = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/refs/heads/main/california_cities_minimal.csv"
CA_CITIES, ZIP_TO_COORD = load_ca_cities_github(GITHUB_URL)

# ------------------ Helper functions ------------------
def parse_job_locations(loc_str):
    if pd.isna(loc_str):
        return []
    return [x.strip().title() for x in str(loc_str).split(',') if x.strip()]

def expand_jobs(df, col_name):
    """Expand rows if a job has multiple cities in the location column"""
    rows = []
    for _, row in df.iterrows():
        cities = parse_job_locations(row[col_name])
        for city in cities:
            new_row = row.copy()
            new_row[col_name] = city
            rows.append(new_row)
    return pd.DataFrame(rows).reset_index(drop=True)

def distance_miles(coord1, coord2):
    return geodesic(coord1, coord2).miles

# ------------------ Upload Job CSV ------------------
uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)

    # ------------------ Ask user which column has city names ------------------
    all_cols = jobs_df.columns.tolist()
    location_col = st.selectbox("Select the column that contains job locations / cities:", all_cols)

    jobs_df = expand_jobs(jobs_df, location_col)

    # ------------------ Candidate Input ------------------
    st.sidebar.header("Search Jobs")
    search_type = st.sidebar.radio("Search by:", ["City", "ZIP Code"])
    search_input = st.sidebar.text_input("Enter your location").strip()
    search_radius = st.sidebar.slider("Search radius (miles)", 1, 100, 50)
    search_btn = st.sidebar.button("Find Jobs")

    if search_btn:
        candidate_coord = None
        if search_type == "City":
            search_input = search_input.title()
            if search_input in CA_CITIES:
                candidate_coord = CA_CITIES[search_input]
            else:
                st.error("Invalid city! Please enter a valid California city.")
        else:  # ZIP Code
            if search_input in ZIP_TO_COORD:
                candidate_coord = ZIP_TO_COORD[search_input]
            else:
                st.error("Invalid ZIP code! Please enter a valid California ZIP.")
        
        if candidate_coord:
            # Map job locations to coordinates
            jobs_df['Job_Coords'] = jobs_df[location_col].apply(lambda x: CA_CITIES.get(x))
            jobs_df = jobs_df.dropna(subset=['Job_Coords']).reset_index(drop=True)

            # Compute distances
            jobs_df['Distance'] = jobs_df['Job_Coords'].apply(lambda x: distance_miles(candidate_coord, x))
            
            # Filter by radius
            filtered_jobs = jobs_df[jobs_df['Distance'] <= search_radius].sort_values('Distance').reset_index(drop=True)

            if filtered_jobs.empty:
                st.warning(f"No jobs found within {search_radius} miles of {search_input}.")
            else:
                st.subheader(f"Jobs within {search_radius} miles of {search_input}:")
                for _, row in filtered_jobs.iterrows():
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #6a11cb, #2575fc); border-radius:12px; padding:15px; margin:10px 0; color:white;">
                        <b>{row.get('client_name', 'Client')} - {row.get('job_title', 'Job Title')}</b><br>
                        {row[location_col]} — {row['Distance']:.1f} mi<br>
                        {''.join([f"<b>{col}:</b> {row[col]}<br>" for col in filtered_jobs.columns if col not in ['Job_Coords','Distance']])}
                    </div>
                    """, unsafe_allow_html=True)

                # Map
                map_data = pd.DataFrame(filtered_jobs['Job_Coords'].tolist(), columns=['lat','lon'])
                map_data['job_title'] = filtered_jobs.get('job_title', '')
                st.map(map_data)
else:
    st.info("Upload a CSV file with job listings to start searching.")
