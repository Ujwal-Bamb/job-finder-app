import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from streamlit_folium import st_folium
import folium
import time

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide")

# ---------------------- ANIMATED WELCOME SCREEN ----------------------
st.markdown("""
    <style>
        body {
            background: linear-gradient(-45deg, #FAD0C4, #FFD1FF, #C2E9FB, #D4FC79);
            background-size: 400% 400%;
            animation: gradientMove 8s ease infinite;
        }

        @keyframes gradientMove {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }

        .welcome-text {
            font-family: 'Trebuchet MS', sans-serif;
            text-align: center;
            font-size: 52px;
            color: white;
            font-weight: bold;
            margin-top: 32vh;
            animation: fadeZoom 2s ease-in-out;
        }

        @keyframes fadeZoom {
            0% {opacity: 0; transform: scale(0.7);}
            100% {opacity: 1; transform: scale(1);}
        }

        .sub-text {
            text-align: center;
            font-size: 22px;
            color: white;
            opacity: 0.85;
            animation: fadeIn 3s ease-in-out;
        }

        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }

        .find-button {
            background-color: #4CAF50;
            color: white;
            font-size: 18px;
            padding: 10px 20px;
            border-radius: 10px;
            border: none;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% {box-shadow: 0 0 0 0 rgba(72, 239, 128, 0.7);}
            70% {box-shadow: 0 0 0 15px rgba(72, 239, 128, 0);}
            100% {box-shadow: 0 0 0 0 rgba(72, 239, 128, 0);}
        }
    </style>
""", unsafe_allow_html=True)

if "show_main" not in st.session_state:
    st.session_state.show_main = False

if not st.session_state.show_main:
    st.markdown('<div class="welcome-text">😊 Keep Smiling Job Finder</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Finding the right job, closer to you 💼</div>', unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.show_main = True
    st.rerun()

# ---------------------- MAIN APP ----------------------
st.title("🌍 Find Nearby Jobs")
st.markdown("Enter candidate location details and find jobs nearby!")

# Input options
col1, col2, col3 = st.columns(3)
with col1:
    zip_code = st.text_input("📍 ZIP Code (optional)")
with col2:
    city = st.text_input("🏙️ City (optional)")
with col3:
    state = st.text_input("🗺️ State (optional)")

radius = st.number_input("🎯 Search Radius (in miles):", min_value=1, max_value=200, value=40)
uploaded_file = st.file_uploader("📂 Upload Job CSV (Client, City, State, Gender, Language)", type=["csv"])

# Find Jobs button
find_button = st.button("🔍 Find Jobs", use_container_width=True)

# ---------------------- FIND JOB LOGIC ----------------------
if find_button:
    if not uploaded_file:
        st.warning("⚠️ Please upload a job CSV file.")
    else:
        with st.spinner("🕵️ Searching nearby jobs..."):
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.lower()

            geolocator = Nominatim(user_agent="job_locator")

            # Determine candidate location
            candidate_coords = None
            if zip_code:
                loc = geolocator.geocode({"postalcode": zip_code, "country": "USA"})
                if loc:
                    candidate_coords = (loc.latitude, loc.longitude)
            if candidate_coords is None and city and state:
                loc = geolocator.geocode(f"{city}, {state}, USA")
                if loc:
                    candidate_coords = (loc.latitude, loc.longitude)

            if candidate_coords is None:
                st.error("❌ Unable to determine candidate location. Enter a valid ZIP or City + State.")
                st.stop()

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

            # Calculate distance
            df["distance_miles"] = df.apply(
                lambda r: geodesic(candidate_coords, (r["latitude"], r["longitude"])).miles
                if pd.notnull(r["latitude"]) and pd.notnull(r["longitude"]) else None,
                axis=1
            )

            # Filter jobs within radius
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
                st.dataframe(nearby_jobs[["client", "city", "state", "gender", "language", "distance_miles"]])
