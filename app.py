import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide")
st.title("😊 Keep Smiling Job Finder")
st.write("Find your next job closer to home 💼")

# ------------------ Predefined California city coordinates ------------------
CA_CITIES = {
    "Los Angeles": (34.0522, -118.2437),
    "San Diego": (32.7157, -117.1611),
    "San Jose": (37.3382, -121.8863),
    "San Francisco": (37.7749, -122.4194),
    "Fresno": (36.7378, -119.7871),
    "Sacramento": (38.5816, -121.4944),
    "Long Beach": (33.7701, -118.1937),
    "Oakland": (37.8044, -122.2711),
    "Bakersfield": (35.3733, -119.0187),
    "Anaheim": (33.8366, -117.9143),
    "Santa Ana": (33.7455, -117.8677),
    "Riverside": (33.9806, -117.3755),
    "Stockton": (37.9577, -121.2908),
    "Chula Vista": (32.6401, -117.0842),
    "Irvine": (33.6846, -117.8265),
    "Fremont": (37.5483, -121.9886),
    "San Bernardino": (34.1083, -117.2898),
    "Modesto": (37.6391, -120.9969),
    "Fontana": (34.0922, -117.4350),
    "Oxnard": (34.1975, -119.1771),
    "Moreno Valley": (33.9425, -117.2297),
    "Glendale": (34.1425, -118.2551),
    "Huntington Beach": (33.6603, -117.9992),
    "Santa Clarita": (34.3917, -118.5426),
    "Garden Grove": (33.7743, -117.9380),
    "Oceanside": (33.1959, -117.3795),
    "Rancho Cucamonga": (34.1064, -117.5931),
    "Santa Rosa": (38.4405, -122.7144),
    "Ontario": (34.0633, -117.6509),
    "Lancaster": (34.6868, -118.1542),
    "Elk Grove": (38.4088, -121.3716),
    "Palmdale": (34.5794, -118.1165),
    "Corona": (33.8753, -117.5664),
    "Salinas": (36.6777, -121.6555),
    "Pomona": (34.0551, -117.7490),
    "Torrance": (33.8358, -118.3406),
    "Hayward": (37.6688, -122.0808),
    "Escondido": (33.1192, -117.0864),
    "Sunnyvale": (37.3688, -122.0363),
    "Pasadena": (34.1478, -118.1445),
    "Fullerton": (33.8704, -117.9243),
    "Orange": (33.7879, -117.8531),
    "Thousand Oaks": (34.1706, -118.8376),
    "Visalia": (36.3302, -119.2921),
    "Simi Valley": (34.2694, -118.7815),
    "Concord": (37.9779, -122.0311),
    "Roseville": (38.7521, -121.2880),
    "Victorville": (34.5361, -117.2912),
    "Santa Clara": (37.3541, -121.9552),
    "Vallejo": (38.1041, -122.2566),
    "Berkeley": (37.8716, -122.2727),
    "El Monte": (34.0686, -118.0276),
    "Downey": (33.9401, -118.1332),
    "Costa Mesa": (33.6411, -117.9187),
    "Inglewood": (33.9617, -118.3531),
    "Carlsbad": (33.1581, -117.3506),
    "San Mateo": (37.5629, -122.3255),
    "Clovis": (36.8252, -119.7020),
    "Compton": (33.8958, -118.2201),
    "Jurupa Valley": (33.9973, -117.4850),
    "Santa Monica": (34.0195, -118.4912),
    "Vista": (33.2000, -117.2426),
    "Mission Viejo": (33.6000, -117.6670),
    "Vacaville": (38.3566, -121.9877),
    "Carson": (33.8317, -118.2817),
    "Hesperia": (34.4264, -117.3003),
    "Rialto": (34.1064, -117.3703),
    "West Covina": (34.0686, -117.9389),
    "Santa Barbara": (34.4208, -119.6982),
    "San Leandro": (37.7249, -122.1561),
    "Chico": (39.7285, -121.8375),
    "Newport Beach": (33.6189, -117.9298)
}

# ------------------ Functions ------------------
def parse_locations(loc_str):
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
                
                # Map visualization
                map_data = pd.DataFrame(df_filtered['Job_Coords'].tolist(), columns=['lat','lon'])
                map_data['job_title'] = df_filtered['job_title']
                st.map(map_data)
else:
    st.info("Upload a CSV file with job listings to start searching.")
