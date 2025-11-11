import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")

# ------------------ Welcome Page ------------------
WELCOME_STYLE = """
<style>
.welcome {
    height:100vh;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    text-align:center;
    font-family:sans-serif;
}
.button-start {
    margin-top:2rem; 
    font-size:1.5rem; 
    padding:1rem 2rem; 
    cursor:pointer; 
    border:none; 
    border-radius:50px;
    background: linear-gradient(90deg, #21d4fd 0%, #b721ff 100%);
    color:white; 
    box-shadow:0 0 15px rgba(183,33,255,0.6); 
    transition: all 0.3s ease;
}
.button-start:hover { 
    box-shadow:0 0 25px rgba(183,33,255,0.9); 
    transform: scale(1.05);
}
h1 { font-size:3.5rem; margin:0; }
h2 { font-weight:normal; font-size:1.5rem; margin-top:0.5rem; color:#555; }
</style>
"""

def show_welcome():
    st.markdown(WELCOME_STYLE, unsafe_allow_html=True)
    st.markdown('<div class="welcome">', unsafe_allow_html=True)
    st.markdown('<h1>😊 Keep Smiling Job Finder</h1>', unsafe_allow_html=True)
    st.markdown('<h2>Find your next opportunity closer to home 💼</h2>', unsafe_allow_html=True)
    if st.button("🚀 Get Started", key="welcome_btn"):
        st.session_state.page = 'main'
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------ Load California Cities ------------------
@st.cache_data
def load_ca_cities(url):
    df = pd.read_csv(url)
    city_dict = {}
    for _, row in df.iterrows():
        city_name = row['city'].strip().title()
        lat, lon = row['lat'], row['lng']
        city_dict[city_name] = (lat, lon)
    return city_dict

GITHUB_URL = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/refs/heads/main/california_cities_minimal.csv"
CA_CITIES = load_ca_cities(GITHUB_URL)

# ------------------ Job CSV Helpers ------------------
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

# ------------------ Job Card Style ------------------
JOB_CARD_STYLE = """
<style>
.job-card {
    background: linear-gradient(135deg, #667eea, #764ba2);
    padding:1rem 1.5rem;
    border-radius:15px;
    margin:0.8rem 0;
    color:white;
    transition: transform 0.2s, box-shadow 0.2s;
    cursor:pointer;
}
.job-card:hover {
    transform: translateY(-5px);
    box-shadow: 0px 8px 25px rgba(0,0,0,0.4);
}
.job-title { font-size:1.3rem; font-weight:600; }
.job-subtitle { font-size:1rem; margin-top:0.2rem; color:#f0f0f0; }
.job-distance { font-size:0.9rem; margin-top:0.5rem; color:#a2ff7d; font-weight:500; }
</style>
"""

# ------------------ Main App ------------------
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'

if st.session_state.page == 'welcome':
    show_welcome()
else:
    st.markdown(JOB_CARD_STYLE, unsafe_allow_html=True)
    st.header("Keep Smiling Job Finder")

    uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])
    if uploaded_file:
        jobs_df = pd.read_csv(uploaded_file)
        jobs_df = expand_jobs(jobs_df, 'location')

        # Sidebar Inputs
        st.sidebar.header("Candidate Location")
        candidate_city = st.sidebar.text_input("Enter your city (California)").strip().title()
        search_radius = st.sidebar.slider("Search radius (miles)", 1, 100, 50)
        search_btn = st.sidebar.button("Find Jobs")

        if search_btn:
            if candidate_city not in CA_CITIES:
                st.error("Invalid city! Enter a valid California city.")
            else:
                candidate_coord = CA_CITIES[candidate_city]

                # Map job locations to coordinates
                jobs_df['Job_Coords'] = jobs_df['location'].apply(lambda x: CA_CITIES.get(x))
                jobs_df = jobs_df.dropna(subset=['Job_Coords']).reset_index(drop=True)

                # Compute distances
                jobs_df['Distance'] = jobs_df['Job_Coords'].apply(lambda x: distance_miles(candidate_coord, x))
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

                    # Map visualization
                    map_data = pd.DataFrame(filtered_jobs['Job_Coords'].tolist(), columns=['lat','lon'])
                    map_data['job_title'] = filtered_jobs['job_title']
                    st.map(map_data)
    else:
        st.info("Upload a CSV file with job listings to start searching.")
