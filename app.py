# app.py
import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide", page_icon="💼")

# --- Simple CSS for styling ---
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg,#e0f2ff,#f5f7ff); font-family: 'Segoe UI', sans-serif; }
.section { background:white; padding:20px 24px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.06); margin-bottom:18px; }
.job-card { background:white; border-radius:12px; padding:14px; margin-bottom:12px; border-left:5px solid #2563eb; }
.center-btn { display:flex; justify-content:center; margin-top:14px; }
.debug { background:#fff3cd; padding:10px; border-radius:8px; color:#663b00; margin-bottom:12px; }
</style>
""", unsafe_allow_html=True)

# ---------- small helper debug logger to page ----------
def debug(msg):
    st.markdown(f"<div class='debug'><b>DEBUG:</b> {msg}</div>", unsafe_allow_html=True)

# ---------- Page routing ----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ---------- Welcome ----------
if st.session_state.page == "welcome":
    st.title("😊 Keep Smiling Job Finder")
    st.markdown("#### Welcome — click to start")
    st.markdown("<div class='section'><h2 style='margin:0'>Keep Smiling Job Finder</h2><p style='margin:0'>Upload job CSV → search by city or ZIP → view nearby jobs.</p></div>", unsafe_allow_html=True)
    if st.button("🚀 Let's Start"):
        st.session_state.page = "main"
        st.rerun()

# ---------- Main ----------
elif st.session_state.page == "main":
    st.title("😊 Keep Smiling Job Finder")
    st.markdown("### Upload CSV and search jobs nearby")

    # ---------------- Load cities CSV (from GitHub)
    @st.cache_data(show_spinner=False)
    def load_ca_cities_github(url):
        try:
            df = pd.read_csv(url)
        except Exception as e:
            return None, None, f"Error reading city CSV: {e}"
        # check required columns
        expected = {"city", "lat", "lng"}
        if not expected.issubset(set(c.lower() for c in df.columns)):
            return None, None, f"City CSV missing required columns. Found: {list(df.columns)}"
        city_dict, zip_dict = {}, {}
        # normalize column names to lower
        cols = {c.lower(): c for c in df.columns}
        for _, row in df.iterrows():
            city_name = str(row[cols["city"]]).strip()
            try:
                lat = float(row[cols["lat"]])
                lng = float(row[cols["lng"]])
            except Exception:
                continue
            city_dict[city_name.lower()] = (lat, lng)
            # zips column optional
            zips_col = cols.get("zips")
            if zips_col and pd.notna(row.get(zips_col)):
                for z in str(row[zips_col]).split():
                    zkey = z.strip()
                    if zkey:
                        zip_dict[zkey] = (lat, lng)
        return city_dict, zip_dict, None

    GITHUB = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/california_cities_minimal.csv"
    CA_CITIES, ZIP_TO_COORD, err = load_ca_cities_github(GITHUB)
    if err:
        st.error(err)
        debug(f"City loader error: {err}")
        st.stop()
    else:
        debug(f"Loaded {len(CA_CITIES)} cities and {len(ZIP_TO_COORD)} zips from city DB")

    # ---------- helpers ----------
    def normalize_display(s):
        return s.strip().title() if isinstance(s, str) else s

    def haversine_miles(coord1, coord2):
        R = 3958.8
        lat1, lon1 = map(radians, coord1)
        lat2, lon2 = map(radians, coord2)
        dlon, dlat = lon2 - lon1, lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    def fuzzy_city_lookup(name):
        if not isinstance(name, str) or not name.strip():
            return None
        key = name.strip().lower().split(",")[0]
        if key in CA_CITIES:
            return CA_CITIES[key]
        # fuzzy match on keys list
        cand = get_close_matches(key, list(CA_CITIES.keys()), n=1, cutoff=0.75)
        if cand:
            return CA_CITIES[cand[0]]
        return None

    # ---------- Upload CSV ----------
    st.markdown("### 📂 Upload your jobs CSV (required column: location)")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if not uploaded:
        st.info("📄 Please upload a CSV file with a 'location' column.")
        st.stop()

    # read jobs CSV with debug
    try:
        jobs_df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Error reading uploaded CSV: {e}")
        debug(f"Uploaded CSV read error: {e}")
        st.stop()

    # normalize headers to lower and stripped
    jobs_df.columns = jobs_df.columns.str.strip().str.lower()
    debug(f"Uploaded CSV columns: {list(jobs_df.columns)}")

    # detect columns
    client_col = next((c for c in jobs_df.columns if "client" in c), None)
    loc_col = next((c for c in jobs_df.columns if "loc" in c or "location" in c), None)
    pos_col = next((c for c in jobs_df.columns if "position" in c or "title" in c), None)
    lang_col = next((c for c in jobs_df.columns if "lang" in c or "language" in c), None)
    pay_col = next((c for c in jobs_df.columns if "pay" in c or "rate" in c), None)
    sched_col = next((c for c in jobs_df.columns if "sched" in c or "schedule" in c), None)

    if not loc_col:
        st.error("Uploaded CSV is missing a location column (expected header like 'location').")
        st.stop()

    # normalize location values (display form)
    jobs_df[loc_col] = jobs_df[loc_col].astype(str).apply(normalize_display)

    # ---------- Search controls on one line ----------
    st.markdown("### 🔍 Search Jobs Near You")
    st.markdown('<div class="section">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 2.4, 1.0])
    with c1:
        # do not use horizontal=True for older streamlit compatibility
        search_type = st.radio("Search by:", ["City", "ZIP Code"])
    with c2:
        if search_type == "City":
            city_input = st.text_input("Enter city name (California)", "")
        else:
            zip_input = st.text_input("Enter ZIP code (5 digits)", "")
    with c3:
        radius = st.slider("Radius (miles)", 1, 100, 50)
    st.markdown('<div class="center-btn">', unsafe_allow_html=True)
    search_btn = st.button("🔍 Find Jobs")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not search_btn:
        st.info("Press Find Jobs to search.")
        st.stop()

    # ---------- Determine candidate_coord (strict ZIP handling) ----------
    candidate_coord = None
    if search_type == "ZIP Code":
        if not zip_input or not zip_input.strip():
            st.error("Please type a ZIP code.")
            st.stop()
        zk = zip_input.strip()
        if zk in ZIP_TO_COORD:
            candidate_coord = ZIP_TO_COORD[zk]
            debug(f"ZIP {zk} matched to coords {candidate_coord}")
        else:
            st.error(f"ZIP '{zk}' not found in database. No fuzzy fallback for ZIPs.")
            debug(f"ZIP lookup failed for '{zk}'. Available sample zips: {list(ZIP_TO_COORD.keys())[:10]}")
            st.stop()
    else:
        if not city_input or len(city_input.strip()) < 2:
            st.error("Please enter at least 2 characters for city.")
            st.stop()
        # try exact (case-insensitive) then fuzzy
        cand = CA_CITIES.get(city_input.strip().lower())
        if cand:
            candidate_coord = cand
            debug(f"City exact match found for '{city_input}' -> {candidate_coord}")
        else:
            fuzzy = fuzzy_city_lookup(city_input)
            if fuzzy:
                candidate_coord = fuzzy
                debug(f"City fuzzy match used for '{city_input}' -> {candidate_coord}")
            else:
                st.error(f"Could not find coordinates for city '{city_input}'. Try different spelling.")
                st.stop()

    # ---------- Map job locations to coords and compute distances ----------
    with st.spinner("Finding nearby jobs..."):
        jobs_df["job_coords"] = jobs_df[loc_col].apply(lambda s: fuzzy_city_lookup(str(s)))
        unknown_count = jobs_df["job_coords"].isna().sum()
        if unknown_count:
            st.warning(f"{unknown_count} job row(s) could not be mapped to coordinates (check 'location' values).")
            debug("Sample unmapped locations: " + ", ".join(jobs_df[jobs_df['job_coords'].isna()][loc_col].unique()[:8].astype(str)))

        jobs_df = jobs_df.dropna(subset=["job_coords"]).reset_index(drop=True)
        if jobs_df.empty:
            st.warning("After mapping, no job rows remain with valid coordinates.")
            st.stop()

        jobs_df["distance"] = jobs_df["job_coords"].apply(lambda x: haversine_miles(candidate_coord, x))
        nearby = jobs_df[jobs_df["distance"] <= radius].sort_values("distance")

    if nearby.empty:
        st.warning(f"No jobs found within {radius} miles.")
        st.stop()

    st.success(f"Found {len(nearby)} job(s) within {radius} miles.")

    # Display expanders: header = Client + Location + Distance; details inside
    for _, r in nearby.iterrows():
        client = (r.get(client_col) or "").strip() if client_col else ""
        loc_display = r.get(loc_col, "")
        dist = r["distance"]
        title = (r.get(pos_col) or "").strip() if pos_col else ""
        header_name = client or (title or "Position")
        label = f"{header_name} — {loc_display} ({dist:.1f} mi)"
        with st.expander(label):
            if title:
                st.markdown(f"**Position:** {title}")
            if client:
                st.markdown(f"**Client:** {client}")
            if pay_col and r.get(pay_col):
                st.markdown(f"**Pay Rate:** {r.get(pay_col)}")
            if lang_col and r.get(lang_col):
                st.markdown(f"**Language:** {r.get(lang_col)}")
            if sched_col and r.get(sched_col):
                st.markdown(f"**Schedule:** {r.get(sched_col)}")
            # show any other columns (non-location, non-coord, non-distance)
            extras = [c for c in jobs_df.columns if c not in (loc_col, "job_coords", "distance")]
            for ex in extras:
                if ex in (client_col, pos_col, pay_col, lang_col, sched_col):
                    continue
                val = r.get(ex)
                if pd.notna(val) and str(val).strip():
                    st.markdown(f"**{ex.title()}:** {val}")

    st.subheader("🗺️ Job Locations Map")
    map_df = pd.DataFrame(nearby["job_coords"].tolist(), columns=["lat", "lon"])
    st.map(map_df)
