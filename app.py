import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from streamlit_folium import st_folium
import folium

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", page_icon="😊", layout="wide")

# ---------------------- CUSTOM ANIMATED HEADER ----------------------
st.markdown(
    """
    <style>
    @keyframes gradientMove {
      0% {background-position: 0% 50%;}
      50% {background-position: 100% 50%;}
      100% {background-position: 0% 50%;}
    }
    .header {
        background: linear-gradient(-45deg, #00b4db, #0083b0, #00b4db, #0083b0);
        background-size: 400% 400%;
        animation: gradientMove 10s ease infinite;
        color: white;
        text-align: center;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .header h1 {
        font-size: 2.8em;
        margin: 0;
    }
    .header p {
        font-size: 1.2em;
        margin-top: 10px;
    }
    </style>
    <div class="header">
        <h1>😊 Keep Smiling – Nearby Job Finder</h1>
        <p>Find your dream job within your area — quickly and happily!</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------- MAIN APP ----------------------
st.sidebar.header("📍 Search Settings")

uploaded_file = st.sidebar.file_uploader("Upload Job CSV File", type=["csv"])

candidate_zip = st.sidebar.text_input("Enter Candidate ZIP Code or City", "")
search_radius = st.sidebar.slider("Search Radius (miles)", 5, 300, 40)

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()

    if "location" not in df.columns:
        st.error("❌ The CSV must contain a 'Location' column.")
        st.stop()

    # Handle multiple job locations
    rows = []
    for _, row in df.iterrows():
        locations = [loc.strip() for loc in str(row["location"]).replace("/", ",").split(",") if loc.strip()]
        for loc in locations:
            new_row = row.copy()
            new_row["location"] = loc
            rows.append(new_row)
    df = pd.DataFrame(rows)

    geolocator = Nominatim(user_agent="job_locator")

    # If user entered ZIP — process it immediately
    if candidate_zip:
        user_location = geolocator.geocode(f"{candidate_zip}, USA")
        if user_location:
            user_coords = (user_location.latitude, user_location.longitude)

            # Geocode job locations
            def get_lat_lon(location):
                try:
                    loc = geolocator.geocode(location + ", USA")
                    if loc:
                        return loc.latitude, loc.longitude
                except:
                    return None, None
                return None, None

            df[["latitude", "longitude"]] = df["location"].apply(lambda x: pd.Series(get_lat_lon(x)))
            df = df.dropna(subset=["latitude", "longitude"])

            # Calculate distances
            df["distance_miles"] = df.apply(
                lambda r: geodesic(user_coords, (r["latitude"], r["longitude"])).miles, axis=1
            )

            nearby_jobs = df[df["distance_miles"] <= search_radius].sort_values("distance_miles")

            # Create map centered at user
            m = folium.Map(location=user_coords, zoom_start=7)
            folium.Marker(
                location=user_coords,
                popup="📍 Candidate Location",
                icon=folium.Icon(color="red", icon="user", prefix="fa"),
            ).add_to(m)

            for _, r in nearby_jobs.iterrows():
                popup = f"""
                <b>Client:</b> {r.get('client','N/A')}<br>
                <b>Location:</b> {r['location']}<br>
                <b>Distance:</b> {round(r['distance_miles'], 2)} miles<br>
                <b>Gender Required:</b> {r.get('gender','N/A')}<br>
                <b>Language:</b> {r.get('language','N/A')}
                """
                folium.Marker(
                    location=[r["latitude"], r["longitude"]],
                    popup=popup,
                    tooltip=f"{r['location']} ({round(r['distance_miles'],1)} mi)",
                    icon=folium.Icon(color="blue", icon="briefcase", prefix="fa"),
                ).add_to(m)

            st.success(f"🎯 Found {len(nearby_jobs)} jobs within {search_radius} miles of {candidate_zip}")
            st_folium(m, width=1100, height=550)
            st.dataframe(nearby_jobs[["client", "location", "gender", "language", "distance_miles"]])
        else:
            st.warning("⚠️ Could not find that ZIP code or city.")
    else:
        st.info("👉 Enter a ZIP code or city to view nearby jobs on the map.")
else:
    st.info("📂 Please upload your job list CSV file from the sidebar to begin.")

# ---------------------- FOOTER ----------------------
st.markdown(
    """
    <hr>
    <div style='text-align:center; color:gray;'>
        Made with ❤️ by <b>Ujwal</b> | Keep Smiling 😊
    </div>
    """,
    unsafe_allow_html=True,
)
