import pandas as pd
jobs_df = pd.read_csv("your_jobs_data.csv")
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="job_board_app")
location = geolocator.geocode("94501")  # Example ZIP
lat, lon = location.latitude, location.longitude
from geopy.distance import geodesic

def distance_between(zip1, zip2):
    loc1 = geolocator.geocode(zip1)
    loc2 = geolocator.geocode(zip2)
    coord1 = (loc1.latitude, loc1.longitude)
    coord2 = (loc2.latitude, loc2.longitude)
    return geodesic(coord1, coord2).miles
jobs_df['match'] = jobs_df['Job Location'].apply(lambda loc: distance_between(user_zip, loc))
filtered_jobs = jobs_df[jobs_df['match'] <= selected_radius]
import streamlit as st

st.header("😊 Welcome to the Job Board!")

user_zip = st.text_input("Enter your ZIP code:")
radius = st.slider("Select search radius (miles):", 10, 100, 25)

if user_zip:
    # geocode user ZIP
    user_location = geolocator.geocode(user_zip)
    if user_location:
        # filter jobs
        filtered_jobs = filter_jobs(user_location, radius, jobs_df)  # define this function
        if not filtered_jobs.empty:
            for idx, job in filtered_jobs.iterrows():
                with st.expander(job['Job Title']):
                    st.write(f"**Client:** {job['Client Name']}")
                    st.write(f"**Location:** {job['Job Location']}")
                    st.write(f"**Agenda:** {job['Agenda']}")
                    st.write(f"**Language:** {job['Language']}")
        else:
            st.write(f"No jobs found within {radius} miles — try increasing your search radius!")
    else:
        st.error("Invalid ZIP code entered.")
