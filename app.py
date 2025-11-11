import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

# Sample job data with multiple locations in one string separated by commas
job_data = {
    'Job Title': ['Data Scientist', 'Software Engineer', 'Project Manager'],
    'Client Name': ['Client A', 'Client B', 'Client C'],
    'Job Location': ['Oakland, Los Angeles, Alameda', 'San Francisco, San Jose', 'Sacramento, Fresno'],
    'Agenda Language': ['English', 'English, Spanish', 'English'],
    'Job Details': [
        'Analyze data and build models.',
        'Develop software applications.',
        'Manage projects and teams.'
    ]
}

df = pd.DataFrame(job_data)

# Initialize geolocator
geolocator = Nominatim(user_agent="job_board_app")

# Cache location lookup for performance
@st.cache_data
def get_location_coords(location):
    try:
        loc = geolocator.geocode(location)
        if loc:
            return (loc.latitude, loc.longitude)
        else:
            return None
    except:
        return None

st.title("😊 Welcome to the Job Board 😊")

candidate_zip = st.text_input("Enter your zip code to find jobs within 50 miles:")

if candidate_zip:
    candidate_coords = get_location_coords(candidate_zip)
    if candidate_coords is None:
        st.error("Invalid or unknown zip code. Please try again.")
    else:
        filtered_jobs = []
        for idx, row in df.iterrows():
            # Split multiple locations and check distances
            job_locations = [loc.strip() for loc in row['Job Location'].split(',')]
            for loc in job_locations:
                loc_coords = get_location_coords(loc)
                if loc_coords:
                    dist = geodesic(candidate_coords, loc_coords).miles
                    if dist <= 50:
                        filtered_jobs.append(row)
                        break

        if filtered_jobs:
            job_selection = st.selectbox("Select a job to see details:", [job['Job Title'] for job in filtered_jobs])
            for job in filtered_jobs:
                if job['Job Title'] == job_selection:
                    st.subheader(job['Job Title'])
                    st.write(f"Client: {job['Client Name']}")
                    st.write(f"Locations: {job['Job Location']}")
                    st.write(f"Agenda Language: {job['Agenda Language']}")
                    st.write(f"Job Details: {job['Job Details']}")
                    break
        else:
            st.info("No jobs found within 50 miles of your location.")
else:
    st.info("Please enter your zip code to search for jobs.")
