import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from streamlit_folium import st_folium
import folium
import time

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide")

# ---------------------- STYLISH ANIMATED WELCOME SCREEN ----------------------
st.markdown("""
    <style>
        body {
            background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #a1c4fd, #c2e9fb);
            background-size: 400% 400%;
            animation: gradientMove 8s ease infinite;
        }
        @keyframes gradientMove {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        .welcome-container {
            text-align: center;
            margin-top: 35vh;
            color: white;
        }
        .welcome-title {
            font-size: 60px;
            font-weight: 900;
            letter-spacing: 2px;
            text-shadow: 0px 0px 15px #ffffff;
            animation: bounce 1.5s infinite alternate;
        }
        @keyframes bounce {
            0% { transform: translateY(0px); }
            100% { transform: translateY(-15px); }
        }
        .sub-text {
            font-size: 24px;
            opacity: 0.9;
            animation: fadeIn 2s ease-in-out;
        }
        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------- INTRO ANIMATION ----------------------
if "show_main" not in st.session_state:
    st.session_state.show_main = False

if not st.session_state.show_main:
    st.markdown("""
        <div class='welcome-container'>
            <div class='welcome-title'>😊 Keep Smiling Job Finder</div>
            <div class='sub-text'>Helping you find your next opportunity, closer to home 💼</div>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.show_main = True
    st.rerun()

# ---------------------- MAIN APP ----------------------
st.title("🌍 Find Nearby Jobs")
st.markdown("Upload your job list, enter candidate location, and find nearby opportunities instantly!")

uploaded_file = st.file_uploader("📂 Upload Job CSV (columns: Client, City, State, Gender, Language, Job_Title, etc.)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()
    st.success(f"✅ Successfully loaded {len(df)} job entries!")

    st.subheader("📍 Candidate Location")
    col1, col2, col3 = st.columns(3)
    with col1:
        zip_code = st.text_input("ZIP Code (optional)")
    with col2:
        city = st.text_input("City (optional)")
    with col3:
        state = st.text_input("State (optional)")

    radius = st.slider("🎯 Search Radius (in miles):", 10, 200, 40)
    find_button = st.button("🔍 Find Nearby Jobs", use_container_width=True)

    geolocator = Nominatim(user_agent="job_locator")

    @st.cache_data(show_spinner=False)
    def get_lat_lon(place):
        """Cached geocoding with improved fallback."""
        try:
            loc = geolocator.geocode(f"{place}, USA", timeout=10)
            if loc:
                return loc.latitude, loc.longitude
        except Exception:
            return None, None
        return None, None

    # ---------------------- WHEN USER CLICKS FIND ----------------------
    if find_button:
        with st.spinner("🕵️ Finding nearby jobs... Please wait..."):
            # Determine candidate location
            candidate_coords = None
            if zip_code:
                candidate_coords = get_lat_lon(str(zip_code))
            if (not candidate_coords) or (None in candidate_coords):
                if city and state:
                    candidate_coords = get_lat_lon(f"{city}, {state}")
            if (not candidate_coords) or (None in candidate_coords):
                st.error("❌ Could not find location for given ZIP/City/State. Please check.")
                st.stop()

            # Geocode job locations
            df["full_location"] = df.apply(lambda r: f"{r.get('city','')}, {r.get('state','')}", axis=1)
            unique_locs = df["full_location"].unique()
            loc_map = {loc: get_lat_lon(loc) for loc in unique_locs}
            df[["latitude", "longitude"]] = df["full_location"].apply(lambda x: pd.Series(loc_map[x]))

            # Calculate distance
            df["distance_miles"] = df.apply(
                lambda r: geodesic(candidate_coords, (r["latitude"], r["longitude"])).miles
                if pd.notnull(r["latitude"]) and pd.notnull(r["longitude"]) else None, axis=1
            )

            nearby = df[df["distance_miles"] <= radius].dropna(subset=["latitude", "longitude"])

            if nearby.empty:
                st.warning("⚠️ No jobs found within that distance.")
            else:
                st.session_state["search_results"] = nearby
                st.session_state["candidate_coords"] = candidate_coords

# ---------------------- DISPLAY RESULTS (PERSISTENT) ----------------------
if "search_results" in st.session_state:
    nearby = st.session_state["search_results"]
    candidate_coords = st.session_state["candidate_coords"]

    st.success(f"✅ Found {len(nearby)} job(s) within your radius!")

    job_list = nearby.reset_index(drop=True)
    selected_job = st.selectbox(
        "🧾 Select a job to view details:",
        [f"{row['client']} - {row.get('job_title','N/A')} ({round(row['distance_miles'],1)} mi)"
         for _, row in job_list.iterrows()],
    )

    if selected_job:
        idx = [f"{row['client']} - {row.get('job_title','N/A')} ({round(row['distance_miles'],1)} mi)"
               for _, row in job_list.iterrows()].index(selected_job)
        job = job_list.iloc[idx]

        st.subheader("📄 Job Details")
        st.markdown(f"""
        **Client:** {job.get('client','N/A')}  
        **Job Title:** {job.get('job_title','N/A')}  
        **City:** {job.get('city','N/A')}  
        **State:** {job.get('state','N/A')}  
        **Gender:** {job.get('gender','N/A')}  
        **Language:** {job.get('language','N/A')}  
        **Schedule:** {job.get('schedule','N/A')}  
        **Distance:** {round(job['distance_miles'],1)} miles
        """)

        col_map1, col_map2 = st.columns(2)
        with col_map1:
            if st.button("🗺️ Show Map for this Job"):
                m = folium.Map(location=candidate_coords, zoom_start=8)
                folium.Marker(candidate_coords, tooltip="Candidate", icon=folium.Icon(color="red")).add_to(m)
                folium.Marker(
                    location=[job["latitude"], job["longitude"]],
                    popup=f"{job['client']} - {job.get('job_title','N/A')}",
                    icon=folium.Icon(color="blue", icon="briefcase", prefix="fa")
                ).add_to(m)
                st_folium(m, width=1000, height=500)

        with col_map2:
            if st.button("🌎 View All Jobs on Map"):
                m2 = folium.Map(location=candidate_coords, zoom_start=6)
                folium.Marker(candidate_coords, tooltip="Candidate", icon=folium.Icon(color="red")).add_to(m2)
                for _, r in job_list.iterrows():
                    folium.Marker(
                        [r["latitude"], r["longitude"]],
                        tooltip=f"{r['client']} ({r['city']})",
                        popup=f"{r['client']} - {r.get('job_title','N/A')}<br>{round(r['distance_miles'],1)} mi away",
                        icon=folium.Icon(color="blue", icon="briefcase")
                    ).add_to(m2)
                st_folium(m2, width=1000, height=500)
else:
    st.info("📤 Upload your CSV and search to see results.")
