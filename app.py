import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# ---------- Streamlit Setup ----------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide", page_icon="😊")

# ---------- CSS Styling ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
    font-family: 'Segoe UI', sans-serif;
    color: #1e293b;
}
h1, h2, h3 {
    color: #1e3a8a;
    font-weight: 700;
}
.section {
    background: white;
    padding: 24px;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
.center {
    text-align: center;
}
.job-expander > div {
    background-color: #f8fafc !important;
    border-radius: 10px;
    border: 1px solid #e2e8f0 !important;
}
div[data-testid="stExpander"] div[role="button"] p {
    font-size: 18px;
    font-weight: 600;
    color: #1e3a8a;
}
div[data-testid="stExpander"] svg {
    color: #2563eb !important;
}
button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1e40af) !important;
    color: white !important;
    border-radius: 8px !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1e40af, #2563eb) !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- State ----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ---------- Welcome Page ----------
if st.session_state.page == "welcome":
    st.markdown("<h1 class='center'>😊 Keep Smiling Job Finder</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='center'>💼 Find your next job closer to home</h3>", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; margin-top:40px;'>
        <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcmY4OHd3bWFuNGY2ZzB6bnRqZDUxaTV2c3oxdm5ybGpnM3p4bHR0aCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xT1R9I7Ne3mAQhXcWc/giphy.gif" width="280" style="border-radius:12px;">
        <p style='margin-top:20px; font-size:18px;'>Upload your job list and find openings near you quickly and easily.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='center'>", unsafe_allow_html=True)
    if st.button("🚀 Let's Start", use_container_width=False):
        st.session_state.page = "main"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Main Job Finder Page ----------
elif st.session_state.page == "main":

    st.title("😊 Keep Smiling Job Finder")
    st.write("Search caregiver job listings by city or ZIP code in California.")

    # ---------- Load City Data ----------
    @st.cache_data(show_spinner=False)
    def load_ca_data():
        url = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/california_cities_minimal.csv"
        df = pd.read_csv(url)
        cities, zips = {}, {}
        for _, row in df.iterrows():
            cities[str(row['city']).strip().lower()] = (row['lat'], row['lng'])
            if pd.notna(row.get('zips', None)):
                for z in str(row['zips']).split():
                    zips[z] = (row['lat'], row['lng'])
        return cities, zips

    CA_CITIES, ZIP_COORDS = load_ca_data()

    # ---------- Helper Functions ----------
    def get_coords(name):
        if not name:
            return None
        name = str(name).strip().lower().split(",")[0]
        if name in CA_CITIES:
            return CA_CITIES[name]
        match = get_close_matches(name, CA_CITIES.keys(), n=1, cutoff=0.75)
        return CA_CITIES[match[0]] if match else None

    def haversine(c1, c2):
        R = 3958.8
        lat1, lon1 = map(radians, c1)
        lat2, lon2 = map(radians, c2)
        dlon, dlat = lon2 - lon1, lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))

    # ---------- Upload CSV ----------
    st.markdown("### 📂 Upload Job List")
    file = st.file_uploader("Upload your CSV file (columns: client, location, language, pay rate, schedule)", type=["csv"])

    if not file:
        st.info("Please upload a CSV to continue.")
        st.stop()

    jobs = pd.read_csv(file)
    jobs.columns = jobs.columns.str.lower().str.strip()

    if 'location' not in jobs.columns:
        st.error("❌ Missing required column: 'location'")
        st.stop()

    # ---------- Search Inputs ----------
    st.markdown("### 🔍 Search Jobs Near You")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_type = st.radio("Search by", ["City", "ZIP Code"], horizontal=True)
    with col2:
        query = st.text_input("Enter City or ZIP", "")
    with col3:
        radius = st.slider("Radius (miles)", 1, 100, 25)

    # ---------- Search Button ----------
    if st.button("🔎 Find Jobs", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a city or ZIP code to search.")
            st.stop()

        # Get user coordinates
        if search_type == "ZIP Code":
            user_coords = ZIP_COORDS.get(query.strip())
        else:
            user_coords = get_coords(query)

        if not user_coords:
            st.error("⚠️ Could not find that city or ZIP in California.")
            st.stop()

        # Compute distances
        jobs["coords"] = jobs["location"].apply(get_coords)
        jobs = jobs.dropna(subset=["coords"])
        jobs["distance"] = jobs["coords"].apply(lambda c: haversine(user_coords, c))
        nearby = jobs[jobs["distance"] <= radius].sort_values("distance")

        # ---------- Show Results ----------
        if nearby.empty:
            st.warning(f"No jobs found within {radius} miles of {query}.")
        else:
            st.success(f"🎯 Found {len(nearby)} job(s) within {radius} miles!")

            for _, row in nearby.iterrows():
                client = row.get("client", "Unknown Client")
                loc = row.get("location", "Unknown Location")
                dist = row["distance"]
                header = f"🧑‍⚕️ {client} — {loc} ({dist:.1f} miles)"

                with st.expander(header, expanded=False):
                    st.markdown(f"**Client:** {client}")
                    st.markdown(f"**Location:** {loc}")
                    st.markdown(f"**Distance:** {dist:.1f} miles")
                    if "positions" in row:
                        st.markdown(f"**Positions:** {row['positions']}")
                    if "language" in row:
                        st.markdown(f"**Language:** {row['language']}")
                    if "pay rate" in row:
                        st.markdown(f"**Pay Rate:** {row['pay rate']}")
                    if "schedule" in row:
                        st.markdown(f"**Schedule:** {row['schedule']}")

            # ---------- Map ----------
            st.subheader("🗺️ Job Locations")
            map_df = pd.DataFrame([{"lat": c[0], "lon": c[1]} for c in nearby["coords"]])
            st.map(map_df)
