"""VoltRoute AI - run with: streamlit run app.py"""
import os
import pandas as pd
import streamlit as st
from ui.styles import CSS

st.set_page_config(page_title="VoltRoute AI — Chennai EV Network", page_icon="⚡", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.session_state.setdefault("view", "landing")
st.session_state.setdefault("page", "Overview")
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)


def load_data():
    """Load the three CSV files; return friendly errors instead of tracebacks."""
    try:
        sites = pd.read_csv("data/ev_locations.csv")
        zones = pd.read_csv("data/demand_zones.csv")
        existing = pd.read_csv("data/existing_stations.csv")
    except FileNotFoundError as e:
        return None, None, None, f"Dataset file missing: {e.filename}. Keep the 'data' folder next to app.py."
    except Exception as e:
        return None, None, None, f"Could not read the dataset: {e}"
    need = {"location_id", "location_name", "latitude", "longitude", "ev_demand", "installation_cost", "station_capacity",
            "grid_capacity", "distance_from_major_road", "land_availability", "existing_station_distance"}
    if sites.empty or zones.empty:
        return None, None, None, "The dataset is empty. Please add rows to data/ev_locations.csv and data/demand_zones.csv."
    if need - set(sites.columns):
        return None, None, None, f"ev_locations.csv is missing columns: {sorted(need - set(sites.columns))}"
    return sites.dropna(), zones.dropna(), existing, None


sites, zones, existing, err = load_data()
if err:
    st.error(err)
    st.stop()
# ==============================================================================
# VIEW ROUTING (LANDING PAGE vs DASHBOARD)
# ==============================================================================
if st.session_state.view == "landing":
    from ui import landing
    landing.render()
else:
    from ui import dashboard
    dashboard.render(sites, zones, existing)
