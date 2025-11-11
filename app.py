import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from streamlit_folium import st_folium
import folium

# ---------------------- PAGE CONFIGURATION ----------------------
st.set_page_config(page_title="Keep Smiling 😊 Job Finder", page_icon="😊", layout="wide")

# ---------------------- TITLE & THEME ----------------------
st.markdown(
    """
    <div style="background-color:#004d99;padding:12px;border-radius:10px;text-align:center">
        <h1 style="color:white;">😊 Keep Smiling – Nearby Job Finder</h1>
        <p style="color:#e6f2ff;font-size:18px;">
            Upload your job listings, enter your ZIP code, and find opportunities within your preferred radius!
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------- FILE UPLOAD ----------------------
uploaded_file = st.file_uploader("📂 Upload your job CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()

    if "location" not in df.columns:
        st.error("❌ The CSV must contain a 'Location' column.")
        st.stop()

    # ---------------------- MULTI-LOCATION HANDLER ----------------------
    rows = []
    for _, row in df.iterrows():
        locations = [loc.strip() for loc in str(row["location"]).replace("/", ",").split(",") if loc.strip()]
        for loc in locations:
            new_row = row.copy()
            new_row["location"] = loc
            rows.append(new_row)

    df = pd.DataFrame(rows)
    st.success(f"✅ Expanded to {len(df)} total job locations!")

    # ---------------------- USER INPUT ----------------------
    col1, col2 = st.columns(2)
    with col1:
        candidate_zip = st.text_input("📍 Enter your ZIP Code or City")
    with col2:
        search_radius = st.number_input("📏 Search Radius (miles)", min_value=5, max_value=500, value=50)

    if candidate_zip:
        geolocator = Nominatim(user_agent="job_locator")
        user_location = geolocator.geocode(f"{candidate_zip}, USA")

        if not user_location:
            st.error("❌ Could not find that ZIP code or city. Please try again.")
            st.stop()

        user_coords = (user_location.latitude, user_location.longitude)

        # ---------------------- GEOCODE JOB LOCATIONS ----------------------
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

        # ---------------------- DISTANCE FILTER ----------------------
        df["distance_miles"] = df.apply(
            lambda row: geodesic(user_coords, (row["latitude"], row["longitude"])).miles, axis=1
        )

        nearby_jobs = df[df["distance_miles"] <= search_radius].sort_values("distance_miles")

        # ---------------------- MAP DISPLAY ----------------------
        m = folium.Map(location=user_coords, zoom_start=7)
        folium.Marker(
            location=user_coords,
            popup="📍 You are here",
            icon=folium.Icon(color="red", icon="user", prefix="fa"),
        ).add_to(m)

        for _, r in nearby_jobs.iterrows():
            popup = f"""
            <b>Client:</b> {r.get('client', 'N/A')}<br>
            <b>Location:</b> {r['location']}<br>
            <b>Distance:</b> {round(r['distance_miles'], 2)} miles<br>
            <b>Role:</b> {r.get('role', 'N/A')}<br>
            <b>Language:</b> {r.get('language', 'N/A')}
            """
            folium.Marker(
                location=[r["latitude"], r["longitude"]],
                popup=popup,
                tooltip=f"{r['location']} ({round(r['distance_miles'], 1)} mi)",
                icon=folium.Icon(color="blue", icon="briefcase", prefix="fa"),
            ).add_to(m)

        st.subheader(f"📊 Found {len(nearby_jobs)} nearby jobs within {search_radius} miles")

        st_folium(m, width=1200, height=600)

        st.dataframe(nearby_jobs[["client", "location", "role", "language", "distance_miles"]])
    else:
        st.info("👆 Enter your ZIP code to start finding jobs near you!")
else:
    st.info("📤 Please upload a CSV file to begin.")

# ---------------------- FOOTER ----------------------
st.markdown(
    """
    <hr>
    <div style='text-align:center; color:gray;'>
        Made with ❤️ by Ujwal | Keep Smiling 😊
    </div>
    """,
    unsafe_allow_html=True,
)
