import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from streamlit_folium import st_folium
import folium
import time

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide")

# ---------------------- CUSTOM CSS (ANIMATION + THEME) ----------------------
st.markdown("""
    <style>
        /* Animated gradient background */
        body {
            background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #fbc2eb, #a6c1ee);
            background-size: 400% 400%;
            animation: gradientBG 10s ease infinite;
        }

        @keyframes gradientBG {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }

        /* Welcome text animation */
        .welcome-text {
            font-size: 48px;
            font-weight: bold;
            color: white;
            text-align: center;
            animation: fadeIn 2s ease-in-out;
            margin-top: 20%;
        }

        @keyframes fadeIn {
            0% {opacity: 0;}
            100% {opacity: 1;}
        }

        /* Animated Let's Start button */
        .start-btn {
            display: block;
            margin: 20px auto;
            background-color: #4CAF50;
            color: white;
            font-size: 22px;
            border: none;
            padding: 15px 40px;
            border-radius: 50px;
            cursor: pointer;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% {box-shadow: 0 0 0 0 rgba(72,239,128,0.7);}
            70% {box-shadow: 0 0 0 20px rgba(72,239,128,0);}
            100% {box-shadow: 0 0 0 0 rgba(72,239,128,0);}
        }

        .start-btn:hover {
            transform: scale(1.05);
            background-color: #45a049;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------- SPLASH SCREEN ----------------------
if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:
    st.markdown('<div class="welcome-text">😊 Keep Smiling Job Finder</div>', unsafe_allow_html=True)
    start = st.button("🚀 Let’s Start", key="start_btn")
    if start:
        st.session_state.started = True
        st.rerun()
    st.stop()

# ---------------------- MAIN PAGE ----------------------
st.title("🌍 Find Nearby Jobs")
st.markdown("Enter your ZIP code and search for job opportunities near you within a chosen distance!")

zip_code = st.text_input("Enter Candidate ZIP Code:")
radius = st.number_input("Enter search radius (in miles):", min_value=1, max_value=200, value=40)
uploaded_file = st.file_uploader("📂 Upload your job CSV file (with columns: Client, Location, City, State, Gender, Language)", type=["csv"])

if uploaded_file is not None and zip_code:
    with st.spinner("🔍 Searching nearby jobs..."):
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.lower()

        geolocator = Nominatim(user_agent="job_locator")

        # Get candidate coordinates
        candidate_location = geolocator.geocode({"postalcode": zip_code, "country": "USA"})
        if candidate_location is None:
            st.error("❌ Could not find the entered ZIP code. Please try again.")
            st.stop()

        candidate_coords = (candidate_location.latitude, candidate_location.longitude)

        # Get job coordinates
        def get_lat_lon(city, state):
            try:
                loc = geolocator.geocode(f"{city}, {state}, USA")
                if loc:
                    return loc.latitude, loc.longitude
            except:
                return None, None
            return None, None

        df[["latitude", "longitude"]] = df.apply(lambda r: pd.Series(get_lat_lon(r.get("city", ""), r.get("state", ""))), axis=1)

        # Filter by distance
        df["distance_miles"] = df.apply(
            lambda r: geodesic(candidate_coords, (r["latitude"], r["longitude"])).miles
            if pd.notnull(r["latitude"]) and pd.notnull(r["longitude"]) else None,
            axis=1
        )

        nearby_jobs = df[df["distance_miles"] <= radius].dropna(subset=["latitude", "longitude"])

        if nearby_jobs.empty:
            st.warning("⚠️ No jobs found within the selected radius.")
        else:
            st.success(f"✅ Found {len(nearby_jobs)} job(s) within {radius} miles!")

            # Display map
            m = folium.Map(location=candidate_coords, zoom_start=8)
            folium.Marker(candidate_coords, tooltip="Candidate Location", icon=folium.Icon(color="red")).add_to(m)

            for _, row in nearby_jobs.iterrows():
                popup = f"<b>Client:</b> {row.get('client','N/A')}<br><b>Location:</b> {row.get('city','N/A')}, {row.get('state','N/A')}<br><b>Distance:</b> {round(row['distance_miles'],1)} miles"
                folium.Marker(
                    location=[row["latitude"], row["longitude"]],
                    popup=popup,
                    icon=folium.Icon(color="blue", icon="briefcase", prefix="fa")
                ).add_to(m)

            st_folium(m, width=1200, height=600)

            # Display job details
            st.dataframe(nearby_jobs[["client", "city", "state", "gender", "language", "distance_miles"]])

else:
    st.info("📍 Please enter ZIP code and upload a CSV to find nearby jobs.")
