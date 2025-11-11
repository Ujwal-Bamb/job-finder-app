import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from streamlit_folium import st_folium
import folium
import time

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide")

# ---------------------- ANIMATED SPLASH PAGE CSS ----------------------
st.markdown("""
    <style>
        body {
            background: linear-gradient(-45deg, #FFDEE9, #B5FFFC, #FEE140, #FA709A);
            background-size: 400% 400%;
            animation: gradientMove 10s ease infinite;
        }

        @keyframes gradientMove {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }

        .welcome-text {
            font-family: 'Trebuchet MS', sans-serif;
            text-align: center;
            font-size: 50px;
            color: white;
            font-weight: 700;
            margin-top: 30vh;
            animation: fadeInZoom 2s ease-in-out;
        }

        @keyframes fadeInZoom {
            0% {opacity: 0; transform: scale(0.8);}
            100% {opacity: 1; transform: scale(1);}
        }

        .sub-text {
            text-align: center;
            font-size: 22px;
            color: white;
            opacity: 0.8;
            animation: fadeIn 2s ease-in-out 0.5s forwards;
        }

        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------- SPLASH SCREEN ----------------------
if "show_main" not in st.session_state:
    st.session_state.show_main = False

if not st.session_state.show_main:
    st.markdown('<div class="welcome-text">😊 Keep Smiling Job Finder</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Connecting candidates to nearby opportunities 💼</div>', unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.show_main = True
    st.rerun()

# ---------------------- MAIN APP ----------------------
st.title("🌍 Find Nearby Jobs")
st.markdown("Enter your ZIP code and discover job opportunities near you!")

zip_code = st.text_input("📍 Enter Candidate ZIP Code:")
radius = st.number_input("🎯 Enter search radius (in miles):", min_value=1, max_value=200, value=40)
uploaded_file = st.file_uploader("📂 Upload your Job CSV file (columns: Client, Location, City, State, Gender, Language)", type=["csv"])

if uploaded_file is not None and zip_code:
    with st.spinner("🔍 Searching for nearby jobs..."):
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.lower()

        geolocator = Nominatim(user_agent="job_locator")

        # Get candidate coordinates
        candidate_location = geolocator.geocode({"postalcode": zip_code, "country": "USA"})
        if candidate_location is None:
            st.error("❌ Invalid ZIP code. Please try again.")
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
