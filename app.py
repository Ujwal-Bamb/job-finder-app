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
.stApp {
    background: linear-gradient(135deg, #e0f2ff, #f5f7ff);
    font-family: 'Segoe UI', sans-serif;
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

# ----------- Page State -----------
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ----------- Welcome Page -----------
if st.session_state.page == "welcome":
    st.markdown("""
    <div style="text-align:center">
        <h1>😊 Keep Smiling Job Finder</h1>
        <h3>💼 Find your next job closer to home</h3>
        <p style="font-size:18px; color:#1e293b;">
            Upload your job list and discover nearby opportunities instantly!
        </p>
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
    uploaded_file = st.file_uploader(
        "Upload your CSV (columns: client_name, location, language, pay_rate, schedule)", 
        type=["csv"]
    )

    if uploaded_file is None:
        st.info("Please upload a CSV to continue.")
        st.stop()

    # --- Push to GitHub ---
    try:
        TOKEN = st.secrets["GITHUB"]["TOKEN"]
        REPO_NAME = st.secrets["GITHUB"]["REPO_NAME"]
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)

        file_content = uploaded_file.getvalue()
        file_path = f"uploads/{uploaded_file.name}"

        try:
            repo.create_file(file_path, f"Upload {uploaded_file.name}", file_content)
            st.success(f"File '{uploaded_file.name}' uploaded to GitHub!")
        except:
            existing_file = repo.get_contents(file_path)
            repo.update_file(existing_file.path, f"Update {uploaded_file.name}", file_content, existing_file.sha)
            st.success(f"File '{uploaded_file.name}' updated in GitHub!")

    except Exception as e:
        st.error(f"⚠️ GitHub upload failed: {e}")

    # --- Download Button for Owner ---
    st.markdown("### 💾 Download Uploaded CSV")
    st.download_button(
        label=f"Download {uploaded_file.name}",
        data=uploaded_file.getvalue(),
        file_name=uploaded_file.name,
        mime="text/csv"
    )

    # --- Process CSV ---
    jobs = pd.read_csv(uploaded_file)
    jobs.columns = jobs.columns.str.lower().str.strip().str.replace(" ", "_")
    if "location" not in jobs.columns:
        st.error("❌ Missing required column: 'location'")
        st.stop()
    jobs["location"] = jobs["location"].astype(str).str.strip().str.lower()
    client_col = next((c for c in jobs.columns if 'client' in c), None)
    jobs['client'] = jobs[client_col] if client_col else "Unknown Client"

    # --- Simple Search Example ---
    st.markdown("### 🔍 Search Jobs by Location")
    query = st.text_input("Enter city or ZIP")
    if query:
        filtered = jobs[jobs["location"].str.contains(query.lower())]
        if filtered.empty:
            st.warning("No jobs found for this location.")
        else:
            for _, row in filtered.iterrows():
                st.markdown(f"""
                <div class='job-card'>
                    <h4>🏥 {row['client']}</h4>
                    <p><b>📍 Location:</b> {row['location']}</p>
                    <p><b>🗣️ Language:</b> {row.get('language', 'N/A')}</p>
                    <p><b>💰 Pay Rate:</b> {row.get('pay_rate', 'N/A')}</p>
                    <p><b>🕒 Schedule:</b> {row.get('schedule', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
