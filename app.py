import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# ---------- Streamlit Setup ----------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide", page_icon="😊")

# ---------- Custom CSS ----------
st.markdown("""
<style>
/* Global page */
.stApp {
    background: linear-gradient(135deg, #e0f2ff, #ffffff);
    font-family: 'Segoe UI', sans-serif;
}

/* Titles */
h1, h2, h3 {
    color: #1e3a8a;
    font-weight: 700;
}

/* Welcome section */
.center {
    text-align: center;
}

button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-size: 18px !important;
    font-weight: 600 !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
}

/* Expander customization */
div[data-testid="stExpander"] {
    background: linear-gradient(145deg, #e6f0ff, #ffffff);
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(37,99,235,0.1);
    margin-bottom: 10px;
}
div[data-testid="stExpander"] div[role="button"] {
    background: linear-gradient(135deg, #60a5fa, #3b82f6);
    border-radius: 12px;
    color: white !important;
    font-weight: 600;
    padding: 10px 16px !important;
}
div[data-testid="stExpander"] svg {
    color: white !important;
}
div[data-testid="stExpander"] p {
    color: #1e293b;
}
</style>
""", unsafe_allow_html=True)

# ---------- State Management ----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ---------- Welcome Page ----------
if st.session_state.page == "welcome":
    st.markdown("<h1 class='center'>😊 Keep Smiling Job Finder</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='center'>💼 Find your next job closer to home</h3>", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; margin-top:50px;'>
        <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcmY4OHd3bWFuNGY2ZzB6bnRqZDUxaTV2c3oxdm5ybGpnM3p4bHR0aCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xT1R9I7Ne3mAQhXcWc/giphy.gif" width="280" style="border-radius:12px;">
        <p style='font-size:18px; margin-top:20px;'>Upload your job list and discover opportunities near you with ease!</p>
    </div>
    """, unsafe_allow_html=True)

    # Centered button
    st.markdown("<div style='display:flex; justify-content:center; margin-top:40px;'>", unsafe_allow_html=True)
    if st.button("🚀 Let's Start", use_container_width=False):
        st.session_state.page = "main"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Main Job Finder Page ----------
elif st.session_state.page == "main":
    st.title("😊 Keep Smiling Job Finder")
    st.write("Search caregiver job listings by city or ZIP code in California.")

    # ---------- Load California Data ----------
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
    file = st.file_uploader("Upload your CSV (columns: client, location, language, pay rate, schedule)", type=["csv"])

    if not file:
        st.info("Please upload a CSV to continue.")
        st.stop()

    jobs = pd.read_csv(file)
    jobs.columns = jobs.columns.str.lower().str.strip()
    if 'location' not in jobs.columns:
        st.error("❌ Missing required column: 'location'")
        st.stop()

    # ---------- Search Controls ----------
    st.markdown("### 🔍 Search Jobs Near You")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_type = st.radio("Search by", ["City", "ZIP Code"], horizontal=True)
    with col2:
        query = st.text_input("Enter City or ZIP", "")
    with col3:
        radius = st.slider("Radius (miles)", 1, 100, 25)

    # ---------- Find Jobs ----------
    if st.button("🔎 Find Jobs", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a city or ZIP code.")
            st.stop()

        if search_type == "ZIP Code":
            user_coords = ZIP_COORDS.get(query.strip())
        else:
            user_coords = get_coords(query)

        if not user_coords:
            st.error("⚠️ Could not find that city or ZIP in California.")
            st.stop()

        jobs["coords"] = jobs["location"].apply(get_coords)
        jobs = jobs.dropna(subset=["coords"])
        jobs["distance"] = jobs["coords"].apply(lambda c: haversine(user_coords, c))
        nearby = jobs[jobs["distance"] <= radius].sort_values("distance")

        if nearby.empty:
            st.warning(f"No jobs found within {radius} miles of {query}.")
        else:
            st.success(f"🎯 Found {len(nearby)} job(s) within {radius} miles!")

            for _, row in nearby.iterrows():
                client = row.get("client", "Unknown Client")
                loc = row.get("location", "Unknown Location")
                dist = row["distance"]
                header = f"🏥 {client} — {loc} ({dist:.1f} miles)"

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
