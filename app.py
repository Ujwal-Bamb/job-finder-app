import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches
from github import Github

# ----------- Streamlit Setup -----------
st.set_page_config(page_title="Keep Smiling Job Finder", layout="wide", page_icon="😊")

# ----------- Custom CSS -----------
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #e0f2ff, #f5f7ff); font-family: 'Segoe UI', sans-serif;}
.job-card {background: white; border-radius:12px; padding:18px; margin:10px 0; box-shadow:0 4px 10px rgba(37,99,235,0.1);}
.job-card h4 {color:#1e3a8a; margin-bottom:8px;}
.job-card p {margin:4px 0; font-size:15px;}
</style>
""", unsafe_allow_html=True)

# ----------- Page State -----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ----------- Welcome Page -----------
if st.session_state.page == "welcome":
    st.markdown("""
    <div style="text-align:center">
        <h1>😊 Keep Smiling Job Finder</h1>
        <h3>💼 Find your next job closer to home</h3>
        <p>Upload your job list and discover nearby opportunities instantly!</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Let's Start"):
            st.session_state.page = "main"
            st.rerun()

# ----------- Main App Page -----------
elif st.session_state.page == "main":
    st.title("😊 Keep Smiling Job Finder")
    
    # --- Upload CSV ---
    st.markdown("### 📂 Upload Job List")
    file = st.file_uploader("Upload your CSV (columns: client_name, location, language, pay_rate, schedule)", type=["csv"])
    
    if file:
        # --- Push uploaded CSV to GitHub ---
        try:
            TOKEN = "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"
            REPO_NAME = "YourUsername/job-finder-app"  # Replace with your GitHub repo
            g = Github(TOKEN)
            repo = g.get_repo(REPO_NAME)
            content = file.getvalue()
            file_path = f"uploads/{file.name}"

            try:
                repo.create_file(file_path, f"Upload {file.name}", content)
                st.success(f"File {file.name} uploaded to GitHub!")
            except:
                existing_file = repo.get_contents(file_path)
                repo.update_file(existing_file.path, f"Update {file.name}", content, existing_file.sha)
                st.success(f"File {file.name} updated in GitHub!")

        except Exception as e:
            st.error(f"GitHub upload failed: {e}")

        # --- Download Button for Owner ---
        st.markdown("### 💾 Download Uploaded CSV")
        st.download_button(
            label=f"Download {file.name}",
            data=file.getvalue(),
            file_name=file.name,
            mime="text/csv"
        )

        # --- Process CSV ---
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
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            search_type = st.radio("Search by", ["City", "ZIP Code"], horizontal=True)
        with col2:
            query = st.text_input("Enter City or ZIP", "").strip()
        with col3:
            radius = st.slider("Radius (miles)", 1, 100, 25)

        def get_coords(name):
            if not name:
                return None
            name = str(name).strip().lower()
            # Minimal hardcoded example; replace with real CA data
            CA_CITIES = {"los angeles": (34.0522, -118.2437), "san francisco": (37.7749, -122.4194)}
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
            return R * 2 * atan2(sqrt(a), sqrt(1 - a))

        if st.button("🔎 Find Jobs"):
            user_coords = get_coords(query)
            if not user_coords:
                st.error("⚠️ Could not find that city or ZIP.")
                st.stop()

            jobs["coords"] = jobs["location"].apply(get_coords)
            jobs = jobs.dropna(subset=["coords"])
            jobs["distance"] = jobs["coords"].apply(lambda c: haversine(user_coords, c))
            nearby = jobs[jobs["distance"] <= radius].sort_values("distance")

            if nearby.empty:
                st.warning(f"No jobs found within {radius} miles of {query}.")
            else:
                st.success(f"🎯 Found {len(nearby)} job(s)!")
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
                            <p><b>🗣️ Language:</b> {row.get('language','N/A')}</p>
                            <p><b>💰 Pay Rate:</b> {row.get('pay_rate','N/A')}</p>
                            <p><b>🕒 Schedule:</b> {row.get('schedule','N/A')}</p>
                        </div>
                        """, unsafe_allow_html=True)
