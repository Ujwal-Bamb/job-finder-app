import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# ---------- Streamlit Setup ----------
st.set_page_config(page_title="😊 Keep Smiling Job Finder", layout="wide", page_icon="💼")

# ---------- CSS Styling ----------
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg,#e0f2ff,#f5f7ff); font-family:'Segoe UI',sans-serif; }
.welcome-box { text-align:center; padding:80px 20px; background:white; border-radius:18px;
    box-shadow:0 6px 20px rgba(0,0,0,0.1); margin-top:60px; margin-bottom:40px; }
.welcome-title { font-size:2.4rem; font-weight:bold; color:#1e3a8a; }
.welcome-sub { font-size:1.1rem; color:#475569; margin-top:10px; }
.section { background:white; padding:20px 30px; border-radius:14px;
    box-shadow:0 4px 10px rgba(0,0,0,0.1); margin-bottom:25px; }
.job-card { background:white; border-radius:16px; box-shadow:0 4px 12px rgba(0,0,0,0.1);
    padding:20px; margin-bottom:15px; border-left:6px solid #2563eb; }
.job-header { font-size:1.1rem; font-weight:bold; color:#1e3a8a; margin-bottom:4px; }
.job-location { color:#475569; font-size:0.95rem; margin-bottom:8px; }
.center-btn { display:flex; justify-content:center; margin-top:30px; }
</style>
""", unsafe_allow_html=True)

# ---------- Page Routing ----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ---------- Welcome Page ----------
if st.session_state.page == "welcome":
    st.markdown(f"""
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

# ---------- Main Page ----------
elif st.session_state.page == "main":
    st.title("😊 Keep Smiling Job Finder")
    st.markdown("### 💼 Find your next job closer to home")

    # ---------- Load City & ZIP Data ----------
    @st.cache_data(show_spinner=False)
    def load_ca_cities_github(url):
        df = pd.read_csv(url)
        city_dict, zip_dict = {}, {}
        for _, r in df.iterrows():
            city_name = str(r["city"]).strip()
            lat, lng = r["lat"], r["lng"]
            # store city keys in lowercase for case-insensitive exact lookup
            city_dict[city_name.lower()] = (lat, lng)
            if pd.notna(r.get("zips", "")):
                for z in str(r["zips"]).split():
                    zkey = z.strip()
                    if zkey:
                        zip_dict[zkey] = (lat, lng)
        return city_dict, zip_dict

    GITHUB_URL = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/california_cities_minimal.csv"
    CA_CITIES, ZIP_TO_COORD = load_ca_cities_github(GITHUB_URL)
    CITY_LIST = sorted([c.title() for c in CA_CITIES.keys()])  # for UI suggestions

    # ---------- Helpers ----------
    def normalize_location(loc):
        return loc.strip().title() if isinstance(loc, str) else loc

    def haversine_miles(c1, c2):
        R = 3958.8
        lat1, lon1 = map(radians, c1)
        lat2, lon2 = map(radians, c2)
        dlon, dlat = lon2 - lon1, lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
