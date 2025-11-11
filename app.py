import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
st.title("😊 Keep Smiling Job Finder")
st.write("Find your next job closer to home 💼")

# ------------------ Predefined CA city coordinates ------------------
CA_CITIES = {
    "Los Angeles": (34.0522, -118.2437),
    "San Francisco": (37.7749, -122.4194),
    "San Diego": (32.7157, -117.1611),
    "San Jose": (37.3382, -121.8863),
    "Concord": (37.9779, -122.0311),
    "Alameda": (37.7652, -122.2416),
    "Fresno": (36.7378, -119.7871),
    "Modesto": (37.6391, -120.9969),
    "Stockton": (37.9577, -121.2908),
    "Sacramento": (38.5816, -121.4944),
    "Oakland": (37.8044, -122.2711),
    "Bakersfield": (35.3733, -119.0187),
    "Anaheim": (33.8366, -117.9143),
    "Santa Clara": (37.3541, -121.9552)
}

# ------------------ Functions ------------------
def parse_locations(loc_str):
    """Split multiple cities if needed"""
    if pd.isna(loc_str):
        return []
    return [x.strip() for x in str(loc_str).split(',') if x.strip()]

def expand_jobs(df, col='location'):
    rows = []
    for _, row in df.iterrows():
        cities = parse_locations(row[col])
        for city in cities:
            new_row = row.copy()
            new_row[col] = city
            rows.append(new_row)
    return pd.DataFrame(rows).reset_index(drop=True)

def get_city_coordinates(city_name):
    return CA_CITIES.get(city_name.strip().title())

def distance_miles(coord1, coord2):
    return geodesic(coord1, coord2).miles

# ------------------ Upload CSV ------------------
uploaded_file = st.file_uploader("Upload your jobs CSV file", type=['csv'])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = expand_jobs(df, 'location')

    # ------------------ Candidate Input ------------------
    st.sidebar.header("Candidate Location")
    candidate_city = st.sidebar.text_input("Enter your City (in California)").strip()
    radius = st.sidebar.slider("Search radius (miles)", 1, 100, 50)
    search_btn = st.sidebar.button("Find Jobs")

    if search_btn:
        candidate_coord = get_city_coordinates(candidate_city)
        if not candidate_coord:
            st.error("Invalid city! Please enter a valid California city.")
        else:
            # ------------------ Calculate distances ------------------
            df['Job_Coords'] = df['location'].apply(get_city_coordinates)
            df = df.dropna(subset=['Job_Coords']).reset_index(drop=True)
            df['Distance'] = df['Job_Coords'].apply(lambda x: distance_miles(candidate_coord, x))
            df_filtered = df[df['Distance'] <= radius].sort_values('Distance').reset_index(drop=True)

            if df_filtered.empty:
                st.warning(f"No jobs found within {radius} miles of {candidate_city}.")
            else:
                st.subheader(f"Jobs within {radius} miles of {candidate_city}:")
                for _, row in df_filtered.iterrows():
                    with st.expander(f"{row['client_name']} - {row['job_title']} ({row['location']}) — {row['Distance']:.1f} mi"):
                        for col in df_filtered.columns:
                            if col not in ['Job_Coords','Distance']:
                                st.write(f"**{col}:** {row[col]}")
                
                # Map
                map_data = pd.DataFrame(df_filtered['Job_Coords'].tolist(), columns=['lat','lon'])
                map_data['job_title'] = df_filtered['job_title']
                st.map(map_data)
else:
    st.info("Upload a CSV file with job listings to start searching.")
