import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Job Finder", layout="wide")

st.title("🌎 Multi-location Job Finder")

uploaded_file = st.file_uploader("Upload your job CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    if "location" not in df.columns:
        st.error("❌ The CSV must contain a 'Location' column.")
        st.stop()

    # Handle multiple locations per client
    rows = []
    for _, row in df.iterrows():
        # Split by comma, slash, or semicolon
        locations = [loc.strip() for loc in str(row["location"]).replace("/", ",").split(",") if loc.strip()]
        for loc in locations:
            new_row = row.copy()
            new_row["location"] = loc
            rows.append(new_row)

    # Create expanded dataframe
    expanded_df = pd.DataFrame(rows)

    st.success(f"✅ Expanded {len(df)} rows to {len(expanded_df)} locations!")

    geolocator = Nominatim(user_agent="job_locator")

    def get_lat_lon(location):
        try:
            loc = geolocator.geocode(location + ", USA")
            if loc:
                return loc.latitude, loc.longitude
        except:
            return None, None
        return None, None

    expanded_df[["latitude", "longitude"]] = expanded_df["location"].apply(lambda x: pd.Series(get_lat_lon(x)))

    map_center = [37.0902, -95.7129]  # USA center
    m = folium.Map(location=map_center, zoom_start=4)

    for _, r in expanded_df.dropna(subset=["latitude", "longitude"]).iterrows():
        popup = f"<b>Client:</b> {r.get('client','N/A')}<br><b>Location:</b> {r['location']}"
        folium.Marker(
            location=[r["latitude"], r["longitude"]],
            popup=popup,
            tooltip=r["location"],
            icon=folium.Icon(color="blue", icon="briefcase", prefix="fa"),
        ).add_to(m)

    st_folium(m, width=1200, height=600)
else:
    st.info("📂 Upload a CSV file with columns like Client, Location, Role, etc.")
