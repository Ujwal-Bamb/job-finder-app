import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from difflib import get_close_matches

# --- Load city + ZIP data ---
@st.cache_data(show_spinner=False)
def load_ca_data():
    # Load cities (broad location reference)
    cities_url = "https://raw.githubusercontent.com/Ujwal-Bamb/job-finder-app/main/california_cities_minimal.csv"
    city_df = pd.read_csv(cities_url)
    city_dict = {str(r["city"]).strip().lower(): (r["lat"], r["lng"]) for _, r in city_df.iterrows()}

    # Load a precise ZIP code dataset (California only)
    zips_url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ca_california_zip_codes_geo.min.csv"
    zip_df = pd.read_csv(zips_url)
    zip_dict = {}
    for _, r in zip_df.iterrows():
        z = str(r["ZCTA5CE10"]).strip()
        lat, lon = r["INTPTLAT"], r["INTPTLONG"]
        try:
            zip_dict[z] = (float(lat), float(lon))
        except:
            continue

    return city_dict, zip_dict
