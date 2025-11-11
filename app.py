import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# ---------------------------------------------
# 🌈 PAGE CONFIG
# ---------------------------------------------
st.set_page_config(
    page_title="😊 Keep Smiling - Nearby Job Finder 🌍",
    page_icon="🧭",
    layout="wide",
)

# ---------------------------------------------
# 🎨 STYLISH HEADER (Animated Gradient)
# ---------------------------------------------
st.markdown(
    """
    <style>
    .title {
        font-size: 42px;
        text-align: center;
        font-weight: bold;
        background: linear-gradient(90deg, #FF6F61, #FFB347);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: slide 3s infinite alternate;
    }
    @keyframes slide {
        from {letter-spacing: 1px;}
        to {letter-spacing: 3px;}
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #444;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    </style>
    <div class="title">😊 Keep Smiling – Nearby Job Finder 🌍</div>
    <div class="subtitle">Find jobs around your ZIP code within 40 miles — quickly, visually, and easily!</div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------
# 📤 FILE UPLOAD SECTION
# ---------------------------------------------
st.sidebar.header("📂 Upload Job Data")
uploaded_file = st.sidebar.file_uploader("Upload a CSV file with job data", type=["csv"])

st.sidebar.markdown(
    """
    **CSV format example:**
    ```
    Job Title,City,State,Gender Required,Language
    Nurse,Chicago,IL,Female,English
    Technician,Dallas,TX,Male,Spanish
    ```
    """
)

# ---------------------------------------------
# 🧭 USER INPUTS
# ---------------------------------------------
st.sidebar.header("📍 Candidate Details")
zip_code = st.sidebar.text_input("Enter your ZIP Code:")
radius = st.sidebar.slider("Select search radius (miles):", 5, 100, 40)

# ---------------------------------------------
# 🌎 PROCESSING LOGIC
# ---------------------------------------------
if uploaded_file and zip_code:
    geolocator = Nominatim(user_agent="job_finder_app")

    try:
        candidate_location = geolocator.geocode(zip_code)
        if not candidate_location:
            st.error("❌ Could not find location for the given ZIP code.")
        else:
            candidate_coords = (candidate_location.latitude, candidate_location.longitude)
            df = pd.read_csv(uploaded_file)

            # Add job coordinates
            st.info("🌍 Locating jobs... please wait a moment ⏳")
            df["Coordinates"] = df.apply(
                lambda row: geolocator.geocode(f"{row['City']}, {row['State']}"), axis=1
            )
            df["Latitude"] = df["Coordinates"].apply(lambda x: x.latitude if x else None)
            df["Longitude"] = df["Coordinates"].apply(lambda x: x.longitude if x else None)

            # Drop missing coordinates
            df = df.dropna(subset=["Latitude", "Longitude"])

            # Calculate distances
            df["Distance (miles)"] = df.apply(
                lambda row: geodesic(candidate_coords, (row["Latitude"], row["Longitude"])).miles,
                axis=1,
            )

            # Filter nearby jobs
            nearby_jobs = df[df["Distance (miles)"] <= radius].sort_values("Distance (miles)")

            # Show results
            st.success(f"🎯 Found {len(nearby_jobs)} job(s) within {radius} miles!")
            st.dataframe(nearby_jobs)

            # Map view
            if len(nearby_jobs) > 0:
                m = folium.Map(location=candidate_coords, zoom_start=8)
                folium.Marker(
                    candidate_coords, tooltip="Candidate Location", icon=folium.Icon(color="blue")
                ).add_to(m)

                for _, row in nearby_jobs.iterrows():
                    folium.Marker(
                        [row["Latitude"], row["Longitude"]],
                        tooltip=f"{row['Job Title']} - {row['City']}, {row['State']}",
                        icon=folium.Icon(color="green"),
                    ).add_to(m)

                st_folium(m, width=700, height=450)
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
else:
    st.info("📥 Upload your CSV and enter your ZIP code to begin.")
