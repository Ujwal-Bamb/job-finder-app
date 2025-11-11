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
        .glow-button {
            font-size:18px;
            padding:10px 25px;
            border:none;
            color:white;
            background:linear-gradient(45deg,#23a6d5,#23d5ab);
            border-radius:12px;
            cursor:pointer;
            box-shadow:0 0 15px #23a6d5;
            transition:all 0.3s ease;
        }
        .glow-button:hover {
            box-shadow:0 0 25px #23d5ab;
            transform:scale(1.05);
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------- ANIMATED INTRO ----------------------
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

# -------- Step 1: Upload CSV --------
uploaded_file = st.file_uploader("📂 Upload Job CSV (columns: Client, City, State, Gender, Language, Job_Title, etc.)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()
    st.success(f"✅ Successfully loaded {len(df)} job entries!")

    # -------- Step 2: Candidate Location Input --------
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
        """Cached geocoding for speed."""
        try:
            loc = geolocator.geocode(f"{place}, USA", timeout=5)
            if loc:
                return loc.latitude, loc.longitude
        except:
            return None, None
        return None, None

    if find_button:
        with st.spinner("🕵️ Finding nearby jobs..."):

            # Step 3: Determine candidate coordinates
            candidate_coords = None
            if zip_code:
                candidate_coords = get_lat_lon(zip_code)
            if not candidate_coords or None in candidate_coords:
                if city and state:
                    candidate_coords = get_lat_lon(f"{city}, {state}")
            if not candidate_coords or None in candidate_coords:
                st.error("❌ Invalid ZIP or City/State. Please try again.")
                st.stop()

            # Step 4: Geocode job locations (fast caching)
            df["full_location"] = df.apply(lambda r: f"{r.get('city','')}, {r.get('state','')}", axis=1)
            unique_locations = df["full_location"].unique()
            loc_dict = {loc: get_lat_lon(loc) for loc in unique_locations}
            df[["latitude", "longitude"]] = df["full_location"].apply(lambda x: pd.Series(loc_dict[x]))

            # Step 5: Compute distances
            df["distance_miles"] = df.apply(
                lambda r: geodesic(candidate_coords, (r["latitude"], r["longitude"])).miles
                if pd.notnull(r["latitude"]) and pd.notnull(r["longitude"]) else None,
                axis=1,
            )

            # Step 6: Filter nearby jobs
            nearby_jobs = df[df["distance_miles"] <= radius].dropna(subset=["latitude", "longitude"])

            if nearby_jobs.empty:
                st.warning("⚠️ No jobs found within that distance.")
            else:
                st.success(f"✅ Found {len(nearby_jobs)} job(s) within {radius} miles!")

                # Step 7: Select job to view details
                job_list = nearby_jobs.reset_index(drop=True)
                selected_job = st.selectbox(
                    "🧾 Select a job to view details:",
                    [f"{row['client']} - {row.get('job_title','N/A')} ({round(row['distance_miles'],1)} mi)"
                     for _, row in job_list.iterrows()],
                )

                if selected_job:
                    index = [f"{row['client']} - {row.get('job_title','N/A')} ({round(row['distance_miles'],1)} mi)"
                             for _, row in job_list.iterrows()].index(selected_job)
                    job = job_list.iloc[index]

                    # Step 8: Show detailed job info
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

                    # Step 9: Ask to show map
                    if st.button("🗺️ Show Map for this Job"):
                        m = folium.Map(location=candidate_coords, zoom_start=8)
                        folium.Marker(candidate_coords, tooltip="Candidate", icon=folium.Icon(color="red")).add_to(m)
                        folium.Marker(
                            location=[job["latitude"], job["longitude"]],
                            popup=f"{job['client']} - {job.get('job_title','N/A')}",
                            icon=folium.Icon(color="blue", icon="briefcase", prefix="fa")
                        ).add_to(m)
                        st_folium(m, width=1200, height=600)

else:
    st.info("📤 Please upload your CSV file to begin.")
