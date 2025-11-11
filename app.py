import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# ---------- Streamlit Setup ----------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide", page_icon="💼")

# ---------- CSS Styling ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#e0f2ff,#f5f7ff);
    font-family:'Segoe UI',sans-serif;
}
.welcome-box {
    text-align:center;padding:80px 20px;background:white;border-radius:18px;
    box-shadow:0 6px 20px rgba(0,0,0,0.1);margin-top:60px;margin-bottom:40px;
}
.welcome-title {
    font-size:2.4rem;font-weight:bold;color:#1e3a8a;
}
.welcome-sub {
    font-size:1.1rem;color:#475569;margin-top:10px;
}
.section {
    background:white;padding:20px 30px;border-radius:14px;
    box-shadow:0 4px 10px rgba(0,0,0,0.1);margin-bottom:25px;
}
.job-card {
    background:white;border-radius:16px;box-shadow:0 4px 12px rgba(0,0,0,0.1);
    padding:20px;margin-bottom:15px;border-left:6px solid #2563eb;
}
.job-header {
    font-size:1.1rem;font-weight:bold;color:#1e3a8a;margin-bottom:4px;
}
.job-location {
    color:#475569;font-size:0.95rem;margin-bottom:8px;
}
.center-btn {display:flex;justify-content:center;margin-top:30px;}
</style>
""", unsafe_allow_html=True)

# ---------- Page Routing ----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ---------- Welcome Page ----------
if st.session_state.page == "welcome":
    st.markdown("""
    <div class="welcome-box">
        <div class="welcome-title">😊 Welcome to Keep Smiling Job Finder</div>
        <div class="welcome-sub">
            Find your dream job closer to home — smart, simple, and beautifully designed.<br>
            Upload your job listings, enter your city or ZIP, and we’ll find nearby opportunities!
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Let's Start"):
            st.session_state.page = "main"
            st.rerun()

# ---------- Main App ----------
elif st.session_state.page == "main":
    st.title("😊 Keep Smiling Job Finder")
    st.markdown("### 💼 Find your next job closer to home")

    # ---------- Load City & ZIP Data ----------
    @st.cache_data(show_spinner=False)
    def load_ca_cities_github(url):
        df = pd.read_csv(url)
        city_dict, zip_dict = {}, {}
        for _, r in df.iterrows():
            city = str(r["city"]).strip().title()
            lat, lng = r["lat"], r["lng"]
            city_dict[city.lower()] = (lat, lng)
            if pd.notna(r["zips"]):
                for z in str(r["zips"]).split():
                    zip_dict[z.strip()] = (lat, lng)
        return city_dict, zip_dict

    GITHUB_URL = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/california_cities_minimal.csv"
    CA_CITIES, ZIP_TO_COORD = load_ca_cities_github(GITHUB_URL)
    CITY_LIST = sorted([c.title() for c in CA_CITIES.keys()])

    # ---------- Helpers ----------
    def normalize_location(loc):
        if isinstance(loc, str):
            return loc.strip().title()
        return loc

    def haversine_miles(c1, c2):
        R = 3958.8
        lat1, lon1 = map(radians, c1)
        lat2, lon2 = map(radians, c2)
        dlon, dlat = lon2 - lon1, lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    def fuzzy_city_lookup(city_name):
        if not isinstance(city_name, str) or not city_name.strip():
            return None
        city_key = city_name.strip().lower().split(",")[0]
        if city_key in CA_CITIES:
            return CA_CITIES[city_key]
        matches = get_close_matches(city_key, list(CA_CITIES.keys()), n=1, cutoff=0.75)
        if matches:
            return CA_CITIES[matches[0]]
        return None

    # ---------- Upload CSV ----------
    st.markdown("### 📂 Upload Job Data")
    uploaded_file = st.file_uploader("Upload your job listings CSV file", type=["csv"])

    if uploaded_file:
        jobs_df = pd.read_csv(uploaded_file)
        jobs_df.columns = jobs_df.columns.str.strip().str.lower()

        # Detect relevant columns (case-insensitive)
        client_col = next((c for c in jobs_df.columns if "client" in c), None)
        loc_col = next((c for c in jobs_df.columns if "loc" in c), None)
        pos_col = next((c for c in jobs_df.columns if "position" in c), None)
        lang_col = next((c for c in jobs_df.columns if "lang" in c), None)
        pay_col = next((c for c in jobs_df.columns if "pay" in c), None)
        sched_col = next((c for c in jobs_df.columns if "sched" in c), None)

        if not loc_col:
            st.error("❌ Could not find a location column in your CSV.")
            st.stop()

        jobs_df[loc_col] = jobs_df[loc_col].apply(normalize_location)

        # ---------- Search Section ----------
        st.markdown("### 🔍 Search Jobs Near You")
        st.markdown('<div class="section">', unsafe_allow_html=True)

        # City/ZIP & Input Field in One Line
        c1, c2, c3 = st.columns([1.2, 2, 1])
        with c1:
            search_type = st.radio("Search by:", ["City", "ZIP Code"], horizontal=True)
        with c2:
            if search_type == "City":
                city_input = st.text_input("Enter city name (California)").strip()
            else:
                zip_input = st.text_input("Enter ZIP code (5 digits)").strip()
        with c3:
            radius = st.slider("Radius (miles)", 1, 100, 50)

        st.markdown('<div class="center-btn">', unsafe_allow_html=True)
        search_btn = st.button("🔍 Find Jobs")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------- Process Search ----------
        if search_btn:
            candidate_coord = None
            if search_type == "City":
                if not city_input:
                    st.error("Please enter a valid city.")
                    st.stop()
                candidate_coord = CA_CITIES.get(city_input.lower()) or fuzzy_city_lookup(city_input)
            else:
                if zip_input in ZIP_TO_COORD:
                    candidate_coord = ZIP_TO_COORD[zip_input]
                else:
                    st.error("ZIP code not found.")
                    st.stop()

            if not candidate_coord:
                st.error("Could not determine location coordinates.")
                st.stop()

            with st.spinner("Finding nearby jobs..."):
                jobs_df["job_coords"] = jobs_df[loc_col].apply(fuzzy_city_lookup)
                jobs_df = jobs_df.dropna(subset=["job_coords"]).reset_index(drop=True)
                jobs_df["distance"] = jobs_df["job_coords"].apply(lambda x: haversine_miles(candidate_coord, x))
                near = jobs_df[jobs_df["distance"] <= radius].sort_values("distance")

            if near.empty:
                st.warning(f"No jobs found within {radius} miles.")
            else:
                st.success(f"🎯 Found {len(near)} job(s) near you!")

                for _, r in near.iterrows():
                    client = r.get(client_col, "Unknown Client") if client_col else "Unknown Client"
                    title = r.get(pos_col, "Position") if pos_col else "Position"
                    city = r.get(loc_col, "Unknown")
                    dist = r["distance"]
                    pay = r.get(pay_col, "")
                    lang = r.get(lang_col, "")
                    sched = r.get(sched_col, "")

                    with st.expander(f"💼 {client} - {title} ({dist:.1f} mi)"):
                        st.markdown(f"""
                        <div class='job-card'>
                            <div class='job-header'>{client} — {title}</div>
                            <div class='job-location'>📍 {city} — {dist:.1f} miles away</div>
                            {f"<b>Pay Rate:</b> {pay}<br>" if pay else ""}
                            {f"<b>Language:</b> {lang}<br>" if lang else ""}
                            {f"<b>Schedule:</b> {sched}<br>" if sched else ""}
                        </div>
                        """, unsafe_allow_html=True)

                st.subheader("🗺️ Job Locations Map")
                map_data = pd.DataFrame(near["job_coords"].tolist(), columns=["lat", "lon"])
                st.map(map_data)
    else:
        st.info("📄 Upload a CSV file with job listings to start searching.")
