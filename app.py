import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import base64

# CSS styles for animations and themes
def local_css():
    st.markdown("""
    <style>
    /* Full screen animated gradient background */
    @keyframes gradientBG {
        0%{background-position:0% 50%;}
        50%{background-position:100% 50%;}
        100%{background-position:0% 50%;}
    }
    .animated-background {
        background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #fad0c4, #ff9a9e);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        height: 100vh;
        width: 100vw;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        overflow: hidden;
        margin: 0;
    }
    /* Glowing gradient text */
    .glow-text {
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(90deg, #ff9a9e, #fad0c4, #ff9a9e);
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
        text-shadow:
          0 0 10px #ff9a9e,
          0 0 20px #ff9a9e,
          0 0 30px #ff9a9e,
          0 0 40px #ff9a9e;
        user-select: none;
    }
    .subtitle {
        font-size: 1.5rem;
        color: white;
        margin-top: -10px;
        margin-bottom: 40px;
        user-select: none;
    }
    /* Pulsing button */
    @keyframes pulse {
      0% {
        box-shadow: 0 0 0 0 rgba(255, 154, 158, 0.7);
      }
      70% {
          box-shadow: 0 0 0 10px rgba(255, 154, 158, 0);
      }
      100% {
          box-shadow: 0 0 0 0 rgba(255, 154, 158, 0);
      }
    }
    .pulse-button {
      font-size: 1.5rem;
      font-weight: 700;
      background: linear-gradient(90deg, #ff9a9e, #fad0c4);
      border: none;
      border-radius: 12px;
      padding: 1rem 3rem;
      color: #5a1a1f;
      cursor: pointer;
      animation: pulse 2s infinite;
      user-select: none;
      transition: background 0.3s ease;
    }
    .pulse-button:hover {
      background: linear-gradient(90deg, #ffbec2, #fcd8d9);
    }
    /* Dark themed main page */
    .dark-theme {
        background-color: #121212;
        color: white;
        min-height: 100vh;
        padding: 3rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Job cards */
    .job-card {
        background-color: #222;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: background-color 0.3s ease;
        color: white;
    }
    .job-card:hover {
        background-color: #333;
    }
    .job-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .job-card-details {
        margin-top: 0.75rem;
        font-size: 1rem;
        display: none;
        white-space: pre-line;
    }
    .job-card.expanded .job-card-details {
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)


# Welcome screen with animated gradient background
def welcome_screen():
    st.markdown("""
    <div class="animated-background">
        <div class="glow-text">😊 Keep Smiling Job Finder</div>
        <div class="subtitle">Find your next opportunity closer to home 💼</div>
        <button class="pulse-button" id="start-btn">Let's Start</button>
    </div>
    <script>
    const btn = window.parent.document.querySelector('button.pulse-button');
    btn.onclick = () => {
        window.parent.postMessage({isStart:true}, '*');
    }
    </script>
    """, unsafe_allow_html=True)


# Parse and expand locations if multiple cities/states or zips are present as lists or strings
def expand_locations(df):
    rows = []
    for _, row in df.iterrows():
        # Assuming Locations column can be a string of comma-separated locations or list-like string
        locations = row.get('Location') or row.get('City') or ""
        if isinstance(locations, str) and (',' in locations or ';' in locations):
            sep = ',' if ',' in locations else ';'
            loc_list = [loc.strip() for loc in locations.split(sep)]
            for loc in loc_list:
                new_row = row.copy()
                # We split into city,state if possible, else use as city.
                if ',' in loc:
                    city, state = [x.strip() for x in loc.split(',', 1)]
                    new_row['City'] = city
                    new_row['State'] = state
                else:
                    new_row['City'] = loc
                    # Keep existing state or empty
                rows.append(new_row)
        else:
            rows.append(row)
    expanded_df = pd.DataFrame(rows)
    return expanded_df.reset_index(drop=True)


# Geocode location to latitude and longitude
@st.cache_data(show_spinner=False)
def geocode_location(city=None, state=None, zipcode=None):
    geolocator = Nominatim(user_agent="keep_smiling_job_finder_app")
    query = ""
    if zipcode:
        query = str(zipcode)
    elif city and state:
        query = f"{city}, {state}"
    elif city:
        query = city
    elif state:
        query = state
    else:
        return None
    try:
        location = geolocator.geocode(query)
        if location:
            return (location.latitude, location.longitude)
        return None
    except:
        return None


# Calculate distance in miles between two lat/lon pairs
def calculate_distance_miles(loc1, loc2):
    try:
        return geodesic(loc1, loc2).miles
    except:
        return None


# Display interactive job cards
def show_job_cards(jobs_df):
    for i, row in jobs_df.iterrows():
        client = row.get('Client', 'N/A')
        job_title = row.get('Job_Title', 'N/A')
        city = row.get('City', 'N/A')
        distance = row.get('Distance', '?')

        card_id = f"card{i}"

        # Show collapsed card header
        card_expanded = st.session_state.get(card_id, False)

        def toggle_card(key=card_id):
            st.session_state[key] = not st.session_state.get(key, False)

        card_container = st.container()
        with card_container:
            header_html = f"""
            <div class='job-card-header'>{client} - {job_title} - {city} - {distance:.1f} miles</div>
            """
            st.markdown(f"<div class='job-card' id='{card_id}' onclick='toggleCard()'>", unsafe_allow_html=True)
            clicked = st.button('View Details' if not card_expanded else 'Hide Details', key=f"btn_{card_id}", on_click=toggle_card)
            st.markdown("</div>", unsafe_allow_html=True)

            if card_expanded:
                detail_text = ""
                for col in jobs_df.columns:
                    detail_text += f"{col}: {row[col]}\n"
                st.markdown(f"<div class='job-card-details'>{detail_text}</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Keep Smiling Job Finder", layout='wide')
    local_css()

    # State to track if user has clicked start
    if 'started' not in st.session_state:
        st.session_state.started = False

    # Welcome screen
    if not st.session_state.started:
        welcome_screen()
        # Hacky workaround: detect button click via JS event
        script = """
            <script>
            const btn = window.parent.document.querySelector('button.pulse-button');
            btn.onclick = () => {
                // Send message to Streamlit to change state
                window.parent.postMessage({func:'startApp'}, '*');
            }
            </script>
        """
        st.markdown(script, unsafe_allow_html=True)
        # Listen to message - not directly possible with Streamlit, so simulate via button
        if st.button("Let's Start"):
            st.session_state.started = True
        return

    # Main job search page
    st.markdown('<div class="dark-theme">', unsafe_allow_html=True)
    st.header("😊 Keep Smiling Job Finder")
    st.subheader("Find your next opportunity closer to home 💼")

    # CSV Upload
    uploaded_file = st.file_uploader("Upload Job CSV File", type=["csv"])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Unable to read CSV file: {e}")
            return

        # Expand locations
        df_expanded = expand_locations(df)

        # Candidate inputs
        with st.form("search_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                zipcode = st.text_input("ZIP Code (optional)").strip()
            with col2:
                city = st.text_input("City (optional)").strip()
            with col3:
                state = st.text_input("State (optional)").strip()

            radius = st.slider("Search Radius (miles)", min_value=0, max_value=200, value=25)

            submitted = st.form_submit_button("Find Jobs Near Me")
            if submitted:
                # Validate inputs
                if not (zipcode or (city and state)):
                    st.warning("Please enter either a ZIP code or both City and State for location search.")
                else:
                    # Geocode candidate location
                    candidate_loc = geocode_location(city=city, state=state, zipcode=zipcode)
                    if not candidate_loc:
                        st.error("Could not determine your location from the inputs provided. Please check and try again.")
                    else:
                        # Geocode each job location and calculate distance
                        distances = []
                        for idx, job_row in df_expanded.iterrows():
                            job_loc = geocode_location(city=job_row.get('City'), state=job_row.get('State'))
                            if job_loc:
                                dist = calculate_distance_miles(candidate_loc, job_loc)
                            else:
                                dist = np.nan
                            distances.append(dist)
                        df_expanded['Distance'] = distances

                        # Filter by distance
                        filtered_df = df_expanded[df_expanded['Distance'] <= radius].copy()
                        if filtered_df.empty:
                            st.info("No jobs found within the specified radius.")
                        else:
                            st.success(f"Found {len(filtered_df)} job(s) within {radius} miles.")
                            show_job_cards(filtered_df)

    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
