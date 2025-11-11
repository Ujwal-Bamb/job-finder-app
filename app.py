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
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
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
uploaded_file = st.file_uploader("📂 Upload Job CSV (columns: Client, City, State, Gender, Language)", type=["csv"])

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

    # Initialize geocoder
    geolocator = Nominatim(user_agent="job_locator")

    # Cache for speed
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

                # Step 7: Create map
                m = folium.Map(location=candidate_coords, zoom_start=8)
                folium.Marker(candidate_coords, tooltip="Candidate", icon=folium.Icon(color="red")).add_to(m)

                for _, row in nearby_jobs.iterrows():
                    popup = f"""
                    <b>Client:</b> {row.get('client','N/A')}<br>
                    <b>City:</b> {row.get('city','N/A')}<br>
                    <b>State:</b> {row.get('state','N/A')}<br>
                    <b>Gender:</b> {row.get('gender','N/A')}<br>
                    <b>Language:</b> {row.get('language','N/A')}<br>
                    <b>Distance:</b> {round(row['distance_miles'],1)} miles
                    """
                    folium.Marker(
                        location=[row["latitude"], row["longitude"]],
                        popup=popup,
                        icon=folium.Icon(color="blue", icon="briefcase", prefix="fa")
                    ).add_to(m)

                # Step 8: Show map and results
                st_folium(m, width=1200, height=600)
                st.dataframe(
                    nearby_jobs[["client", "city", "state", "gender", "language", "distance_miles"]]
                    .sort_values("distance_miles")
                    .reset_index(drop=True)
                )

else:
    st.info("📤 Please upload your CSV file to begin.")
