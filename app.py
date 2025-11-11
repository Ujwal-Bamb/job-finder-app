import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# ---------- Streamlit Setup ----------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide", page_icon="💼")

# ---------- Custom CSS ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #e0f7ff, #f5f7ff);
    font-family: 'Segoe UI', sans-serif;
}
h1, h2, h3 {
    color: #1e3a8a;
}
.job-card {
    background: linear-gradient(135deg, #6a11cb, #2575fc);
    color: white;
    padding: 18px;
    border-radius: 14px;
    margin-bottom: 14px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.job-header {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 6px;
}
.job-sub {
    font-size: 14px;
    opacity: 0.9;
}
.expander-content {
    background: white;
    color: black;
    padding: 14px;
    border-radius: 10px;
    margin-top: 8px;
}
.center {
    text-align: center;
}
button[kind="primary"] {
    border-radius: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- App State ----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ---------- Helper Functions ----------
def haversine(coord1, coord2):
    R = 3958.8
    lat1, lon1 = map(radians, coord1)
    lat2, lon2 = map(radians, coord2)
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def normalize(s):
    return str(s).strip().lower() if isinstance(s, str) else s

def get_coords(name, city_dict):
    if not name: return None
    name = normalize(name.split(",")[0])
    if name in city_dict:
        return city_dict[name]
    close = get_close_matches(name, city_dict.keys(), n=1, cutoff=0.75)
    return city_dict[close[0]] if close else None

# ---------- Load CA Cities ----------
@st.cache_data(show_spinner=False)
def load_ca_data():
    url = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/california_cities_minimal.csv"
    df = pd.read_csv(url)
    city_dict, zip_dict = {}, {}
    for _, row in df.iterrows():
        city_dict[str(row["city"]).lower()] = (row["lat"], row["lng"])
        if pd.notna(row.get("zips", "")):
            for z in str(row["zips"]).split():
                zip_dict[z] = (row["lat"], row["lng"])
    return city_dict, zip_dict

CA_CITIES, ZIP_COORDS = load_ca_data()

# ---------- Welcome Page ----------
if st.session_state.page == "welcome":
    st.markdown("<h1 class='center'>😊 Keep Smiling Job Finder</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='center'>💼 Find your next job closer to home</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div class='center' style='margin-top:40px;'>
        <img src="https://media.giphy.com/media/xT1R9I7Ne3mAQhXcWc/giphy.gif" width="260"><br><br>
        <p style='font-size:18px;'>Upload your job list and start exploring nearby opportunities.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Let's Start", use_container_width=True):
        st.session_state.page = "main"
        st.rerun()

# ---------- Main Page ----------
elif st.session_state.page == "main":

    st.title("😊 Keep Smiling Job Finder")
    st.markdown("Easily explore caregiver job listings near your area in California!")

    # ---- File Upload ----
    st.markdown("### 📂 Upload Job CSV")
    file = st.file_uploader("Upload CSV (with columns like Client_name, Location, Language, Pay Rate, Schedule)", type=['csv'])
    if not file:
        st.info("Please upload your CSV file to continue.")
        st.stop()

    jobs = pd.read_csv(file)
    jobs.columns = [c.strip().lower() for c in jobs.columns]
    if "location" not in jobs.columns:
        st.error("Your CSV must include a 'location' column.")
        st.stop()

    # ---- Search Inputs ----
    st.markdown("### 🔍 Search Jobs Near You")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_type = st.radio("Search by", ["City", "ZIP Code"], horizontal=True)
    with col2:
        user_input = st.text_input("Enter your City or ZIP Code", "")
    with col3:
        radius = st.slider("Radius (miles)", 1, 100, 25)

    # ---- Search Button ----
    if st.button("🔎 Find Jobs", use_container_width=True):
        if not user_input:
            st.error("Please enter a city or ZIP code.")
            st.stop()

        user_coords = None
        if search_type == "ZIP Code":
            user_coords = ZIP_COORDS.get(user_input.strip())
        else:
            user_coords = get_coords(user_input, CA_CITIES)

        if not user_coords:
            st.error("Location not found in California.")
            st.stop()

        # ---- Distance Calculation ----
        jobs["coords"] = jobs["location"].apply(lambda x: get_coords(x, CA_CITIES))
        jobs = jobs.dropna(subset=["coords"])
        jobs["distance"] = jobs["coords"].apply(lambda c: haversine(user_coords, c))

        filtered = jobs[jobs["distance"] <= radius].sort_values("distance")

        if filtered.empty:
            st.warning(f"No jobs found within {radius} miles.")
        else:
            st.success(f"🎯 Found {len(filtered)} job(s) within {radius} miles of your location.")
            for _, row in filtered.iterrows():
                client = row.get("client_name", "Unknown Client")
                loc = row.get("location", "Unknown Location")
                dist = row["distance"]

                st.markdown(f"""
                <div class='job-card'>
                    <div class='job-header'>{client} — {loc} ({dist:.1f} miles away)</div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("View Details"):
                    st.markdown(f"<div class='expander-content'>", unsafe_allow_html=True)
                    if "positions" in row: st.write(f"**Positions:** {row['positions']}")
                    if "language" in row: st.write(f"**Language:** {row['language']}")
                    if "pay rate" in row: st.write(f"**Pay Rate:** {row['pay rate']}")
                    if "schedule" in row: st.write(f"**Schedule:** {row['schedule']}")
                    st.markdown("</div>", unsafe_allow_html=True)

            # ---- Optional Map ----
            st.subheader("🗺️ Job Locations")
            map_df = pd.DataFrame([{"lat": c[0], "lon": c[1]} for c in filtered["coords"]])
            st.map(map_df)
