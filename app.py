import streamlit as st
import pandas as pd
from geopy.distance import geodesic

# ------------------ Page Config ------------------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")

st.markdown(
    """
    <style>
    body {background-color: #0E1117; color: #FFFFFF; font-family: 'Segoe UI', sans-serif;}
    .stButton>button {background-color:#FF4B4B; color:white; height:3em; width:100%; font-size:16px; border-radius:12px;}
    .stSlider>div>div>div>div {color:#FF4B4B;}
    .job-card {background: linear-gradient(135deg, #6a11cb, #2575fc); border-radius:12px; padding:15px; margin:10px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition: all 0.2s ease-in-out;}
    .job-card:hover {transform: scale(1.03); box-shadow: 0 6px 20px rgba(255,75,75,0.5);}
    .job-title {font-size:1.3rem; font-weight:bold; color:white;}
    .job-sub {font-size:1rem; color:#FFD700; margin-bottom:5px;}
    </style>
    """, unsafe_allow_html=True
)

st.title("😊 Keep Smiling Job Finder")
st.markdown("Find your next job closer to home 💼")

# ------------------ Load California Cities with ZIPs ------------------
@st.cache_data
def load_ca_cities_github(url):
    df = pd.read_csv(url)
    city_dict = {}
    zip_dict = {}
    for _, row in df.iterrows():
        city_name = row['city'].strip().title()
        lat, lon = row['lat'], row['lng']
        city_dict[city_name] = (lat, lon)
        # Handle multiple zip codes
        if pd.notna(row['zips']):
            for z in str(row['zips']).split():
                zip_dict[z] = (lat, lon)
    return city_dict, zip_dict

GITHUB_URL = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/refs/heads/main/california_cities_minimal.csv"
CA_CITIES, ZIP_TO_COORD = load_ca_cities_github(GITHUB_URL)

# ------------------ Job helper functions ------------------
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

# ------------------ Upload Job CSV ------------------
uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)
    jobs_df = expand_jobs(jobs_df, 'location')

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
            jobs_df['Job_Coords'] = jobs_df['location'].apply(lambda x: CA_CITIES.get(x))
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
                    <div class="job-card">
                        <div class="job-title">{row['client_name']} - {row['job_title']}</div>
                        <div class="job-sub">{row['location']} — {row['Distance']:.1f} mi</div>
                        <div>{''.join([f"<b>{col}:</b> {row[col]}<br>" for col in filtered_jobs.columns if col not in ['Job_Coords','Distance']])}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Map
                map_data = pd.DataFrame(filtered_jobs['Job_Coords'].tolist(), columns=['lat','lon'])
                map_data['job_title'] = filtered_jobs['job_title']
                st.map(map_data)
else:
    st.info("Upload a CSV file with job listings to start searching.")
