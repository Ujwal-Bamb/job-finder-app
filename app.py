from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches
import streamlit as st
import pandas as pd
from github import Github  # GitHub API

# ----------- Streamlit Setup -----------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide", page_icon="😊")

# ----------- Enhanced Custom CSS -----------
st.markdown("""<style> ... </style>""", unsafe_allow_html=True)  # Your existing CSS

# ----------- Streamlit Page State -----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ----------- Welcome Page -----------
if st.session_state.page == "welcome":
    st.markdown("""<style> ... </style>""", unsafe_allow_html=True)
    st.write("")
    st.write("")
    st.markdown("""<div style="text-align:center">
                    <h1>😊 Keep Smiling Job Finder</h1>
                    <h3>💼 Find your next job closer to home</h3>
                    <img src="https://media.giphy.com/media/xT1R9I7Ne3mAQhXcWc/giphy.gif" width="260" style="border-radius:12px; margin:25px 0;">
                    <p style="font-size:18px; color:#1e293b;">Upload your job list and discover nearby opportunities instantly!</p>
                  </div>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Let's Start", key="start-main"):
            st.session_state.page = "main"
            st.rerun()

# ----------- Main App Page -----------
elif st.session_state.page == "main":
    st.title("😊 Keep Smiling Job Finder")
    st.write("Search caregiver job listings by city or ZIP code in California.")

    # --- Load California city/ZIP data ---
    @st.cache_data(show_spinner=False, ttl=3600)
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
        if not c1 or not c2:
            return float('inf')
        R = 3958.8
        lat1, lon1 = map(radians, c1)
        lat2, lon2 = map(radians, c2)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    # --- Upload Jobs CSV ---
    st.markdown("### 📂 Upload Job List")
    file = st.file_uploader("Upload your CSV (columns: client_name, location, language, pay rate, schedule)", type=["csv"])

    if not file:
        st.info("Please upload a CSV to continue.")
        st.stop()

    # --- Push uploaded CSV to GitHub ---
    try:
        TOKEN = st.secrets["GITHUB_TOKEN"]
        REPO_NAME = "username/repo"  # replace with your repo
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)

        content = file.getvalue()
        file_path = f"uploads/{file.name}"

        try:
            repo.create_file(file_path, f"Upload {file.name}", content)
            st.success(f"File {file.name} uploaded to GitHub!")
        except:
            # If file exists, update it
            existing_file = repo.get_contents(file_path)
            repo.update_file(existing_file.path, f"Update {file.name}", content, existing_file.sha)
            st.success(f"File {file.name} updated in GitHub!")

    except Exception as e:
        st.error(f"⚠️ GitHub upload failed: {e}")

    # --- Process CSV for job search ---
    jobs = pd.read_csv(file)
    jobs.columns = jobs.columns.str.lower().str.strip().str.replace(" ", "_")
    if 'location' not in jobs.columns:
        st.error("❌ Missing required column: 'location'")
        st.stop()
    jobs['location'] = jobs['location'].astype(str).str.strip().str.lower()
    client_col = next((c for c in jobs.columns if 'client' in c), None)
    jobs['client'] = jobs[client_col] if client_col else "Unknown Client"

    # --- Search UI ---
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
        user_coords = ZIP_COORDS.get(query) if search_type=="ZIP Code" else get_coords(query)
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
