import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from streamlit_folium import st_folium
import folium
import time

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Keep Smiling 😊 Job Finder", page_icon="😊", layout="wide")

# ---------------------- ANIMATED WELCOME PAGE ----------------------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

if st.session_state.page == "welcome":
    st.markdown(
        """
        <style>
        @keyframes fadeIn {
            from {opacity: 0; transform: translateY(20px);}
            to {opacity: 1; transform: translateY(0);}
        }
        .welcome-container {
            background: linear-gradient(135deg, #00b4db, #0083b0);
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            text-align: center;
            animation: fadeIn 2s ease-in-out;
        }
        .title {
            font-size: 3em;
            font-weight: bold;
            animation: fadeIn 2s ease-in-out;
        }
        .subtitle {
            font-size: 1.3em;
            margin-top: 10px;
            animation: fadeIn 3s ease-in-out;
        }
        .emoji {
            font-size: 4em;
            margin-top: 20px;
            animation: fadeIn 2s ease-in-out infinite alternate;
        }
        </style>
        <div class="welcome-container">
            <div class="emoji">😊</div>
            <div class="title">Keep Smiling Job Finder</div>
            <div class="subtitle">Find your next opportunity within miles — easily and happily!</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    time.sleep(1.5)
    if st.button("Let's Start 🚀", use_container_width=True):
        st.session_state.page = "main"
        st.rerun()

# ---------------------- MAIN APP PAGE ----------------------
elif st.session_state.page == "main":

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

    uploaded_file = st.file_uploader("📂 Upload your job CSV file", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.lower()

        if "location" not in df.columns:
            st.error("❌ The CSV must contain a 'Location' column.")
            st.stop()

        rows = []
        for _, row in df.iterrows():
            locations = [loc.strip() for loc in str(row["location"]).replace("/", ",").split(",") if loc.strip()]
            for loc in locations:
                new_row = row.copy()
                new_row["location"] = loc
                rows.append(new_row)

        df = pd.DataFrame(rows)
        st.success(f"✅ Expanded to {len(df)} total job locations!")

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

            df["distance_miles"] = df.apply(
                lambda row: geodesic(user_coords, (row["latitude"], row["longitude"])).miles, axis=1
            )

            nearby_jobs = df[df["distance_miles"] <= search_radius].sort_values("distance_miles")

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

    st.markdown(
        """
        <hr>
        <div style='text-align:center; color:gray;'>
            Made with ❤️ by Ujwal | Keep Smiling 😊
        </div>
        """,
        unsafe_allow_html=True,
    )
