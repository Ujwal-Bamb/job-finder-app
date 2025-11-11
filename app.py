import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# ----------- Streamlit Setup -----------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide", page_icon="😊")

# ----------- Enhanced Custom CSS -----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #e0f2ff, #f5f7ff);
    font-family: 'Segoe UI', sans-serif;
}
.center-welcome {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 89vh;
    width: 100%;
}
.big-btn button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 18px 50px !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 18px rgba(37,99,235,0.13);
    margin-top: 34px;
    border: none !important;
}
.big-btn button:hover {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    transform: scale(1.07);
}
div[data-testid="stExpander"] {
    background: linear-gradient(145deg, #f8fbff, #e6f0ff);
    border: 1px solid #bfdbfe;
    border-radius: 15px;
    box-shadow: 0 6px 12px rgba(37,99,235,0.1);
    margin-bottom: 15px;
    overflow: hidden;
}
div[data-testid="stExpander"] div[role="button"] {
    background: linear-gradient(135deg, #60a5fa, #3b82f6);
    border-radius: 15px 15px 0 0;
    color: white !important;
    font-weight: 600;
    padding: 14px 18px !important;
    font-size: 17px;
}
div[data-testid="stExpander"] p {
    color: #1e293b;
}
.job-card {
    background: white;
    border-radius: 12px;
    padding: 18px;
    margin: 10px 0;
    box-shadow: 0 4px 10px rgba(37,99,235,0.1);
}
.job-card h4 {
    color: #1e3a8a;
    margin-bottom: 8px;
}
.job-card p {
    margin: 4px 0;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

# ----------- Streamlit Page State -----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ----------- Welcome Page -----------
if st.session_state.page == "welcome":
    st.markdown("""
    <div class="center-welcome">
        <h1>😊 Keep Smiling Job Finder</h1>
        <h3>💼 Find your next job closer to home</h3>
        <img src="https://media.giphy.com/media/xT1R9I7Ne3mAQhXcWc/giphy.gif" width="260" style="border-radius:12px; margin:25px 0;">
        <p style="font-size:18px; color:#1e293b;">Upload your job list and discover nearby opportunities instantly!</p>
        <div class="big-btn">
    """, unsafe_allow_html=True)

    if st.button("🚀 Let's Start", key="start-main"):
        st.session_state.page = "main"
        st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

# ----------- Main App Page -----------
elif st.session_state.page == "main":
    st.title("😊 Keep Smiling Job Finder")
    st.write("Search caregiver job listings by city or ZIP code in California.")

    # --- Load California city/ZIP data ---
    @st.cache_data(show_spinner=False)
    def load_ca_data():
        url = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/california_cities_minimal.csv"
        df = pd.read_csv(url)
        cities, zips = {}, {}
        for _, row in df.iterrows():
            cities[str(row['city']).strip().lower()] = (row['lat'], row['lng'])
            if pd.notna(row.get('zips', None)):
                for z in str(row['zips']).split():
                    zips[z.strip()] = (row['lat'], row['lng'])
        return cities, zips

    CA_CITIES, ZIP_COORDS = load_ca_data()

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
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a)

    # --- Upload Jobs CSV ---
    st.markdown("### 📂 Upload Job List")
    file = st.file_uploader("Upload your CSV (columns: client_name, location, language, pay rate, schedule)", type=["csv"])

    if not file:
        st.info("Please upload a CSV to continue.")
        st.stop()

    jobs = pd.read_csv(file)
    jobs.columns = jobs.columns.str.lower().str.strip().str.replace(" ", "_")

    if 'location' not in jobs.columns:
        st.error("❌ Missing required column: 'location'")
        st.stop()

    jobs['location'] = jobs['location'].astype(str).str.strip().str.lower()

    client_col = next((c for c in jobs.columns if 'client' in c), None)
    if client_col:
        jobs['client'] = jobs[client_col]
    else:
        jobs['client'] = "Unknown Client"

    st.markdown("### 🔍 Search Jobs Near You")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_type = st.radio("Search by", ["City", "ZIP Code"], horizontal=True)
    with col2:
        query = st.text_input("Enter City or ZIP", "").strip()
    with col3:
        radius = st.slider("Radius (miles)", 1, 100, 25)

    if st.button("🔎 Find Jobs", use_container_width=True):
        if not query:
            st.warning("Please enter a city or ZIP code.")
            st.stop()
        if search_type == "ZIP Code":
            if not query.isdigit() or len(query) != 5:
                st.error("Please enter a valid 5-digit ZIP code.")
                st.stop()
            user_coords = ZIP_COORDS.get(query)
        else:
            user_coords = get_coords(query)
        if not user_coords:
            st.error("⚠️ Could not find that city or ZIP in California.")
            st.stop()
        jobs["coords"] = jobs["location"].apply(get_coords)
        missing = jobs["coords"].isna().sum()
        if missing > 0:
            st.warning(f"{missing} job(s) not matched to any city (excluded).")
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
                with st.expander(header):
                    st.markdown(f"""
                    <div class='job-card'>
                        <h4>🏥 {client}</h4>
                        <p><b>📍 Location:</b> {loc}</p>
                        <p><b>📏 Distance:</b> {dist:.1f} miles</p>
                        <p><b>👥 Positions:</b> {row.get('positions', 'N/A')}</p>
                        <p><b>🗣️ Language:</b> {row.get('language', 'N/A')}</p>
                        <p><b>💰 Pay Rate:</b> {row.get('pay_rate', 'N/A')}</p>
                        <p><b>🕒 Schedule:</b> {row.get('schedule', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            st.subheader("🗺️ Job Locations")
            map_df = pd.DataFrame([{"lat": c[0], "lon": c[1]} for c in nearby["coords"]])
            st.map(map_df)
