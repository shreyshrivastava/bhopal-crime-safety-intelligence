"""
================================================================================
Bhopal Safety Intelligence Portal
Material Active (M3 Adaptive) Web Application
================================================================================
Target Geography: Bhopal, Madhya Pradesh, India (23.2599° N, 77.4126° E)
Core Engines: Leaflet.js, ESRI World Street Maps, Pandas, GeoPandas, Streamlit
Features:
- Material Active UI with dynamic data connections
- Civic Safety Incident Registry & KPI overview cards
- Interactive Leaflet geospatial engine with Marker Clustering & Kernel Density Heatmap
- Multi-parametric filters (Category, Time of Day, Zone/Ward, Severity score threshold)
- Safety post proximity radar (10 Thanas) & Civic Safe Corridors
- Multidimensional civic risk analytics & offense modality distributions
- Sector Safety & Proximity index ranking table
- Filtered Crime Records Explorer with text search and CSV export
- Direct navigation linking (Map, Analyze, Hotspots, Records, SOS)
================================================================================
"""

import os
# Ensure macOS ARM64 / Apple Silicon fork safety for multithreaded servers
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["PROJ_NETWORK"] = "OFF"

import json
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import geopandas as gpd

# Domain modules
from data_generator import (
    generate_crime_dataset,
    to_geodataframe,
    POLICE_STATIONS,
    SAFE_CORRIDORS,
    NEIGHBORHOOD_CONFIG
)
from spatial_analytics import (
    calculate_station_proximity,
    compute_sector_risk_index
)
import importlib
import ui_builder
importlib.reload(ui_builder)
from ui_builder import generate_material_active_html

# ==============================================================================
# STREAMLIT CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Bhopal Safety Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Zero-margin styling for full-bleed Material Active canvas
STREAMLIT_CONTAINER_STYLE = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden; height: 0 !important; margin: 0 !important; padding: 0 !important;}
    footer {visibility: hidden; height: 0 !important;}
    html, body, .stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"], section.main, .main, .block-container {
        height: 100vh !important;
        max-height: 100vh !important;
        overflow: hidden !important;
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        background-color: #0b0f17 !important;
        background: #0b0f17 !important;
    }
    div[data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    div[data-testid="stCustomComponentV1"], .stCustomComponentV1, iframe {
        width: 100vw !important;
        height: 100vh !important;
        max-height: 100vh !important;
        border: none !important;
        display: block !important;
        background-color: #0b0f17 !important;
        background: #0b0f17 !important;
    }
</style>
"""
st.markdown(STREAMLIT_CONTAINER_STYLE, unsafe_allow_html=True)


# ==============================================================================
# DATA INGESTION & CACHING PIPELINE (24h Daily Rolling Synchronization)
# ==============================================================================
@st.cache_data(ttl=86400, show_spinner=False)
def load_bhopal_data(num_samples: int = 520, random_seed: int = 101, date_str: str = None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    ref_date = datetime.strptime(date_str, "%Y-%m-%d")
    raw_df = generate_crime_dataset(n_samples=num_samples, seed=random_seed, reference_date=ref_date)
    gdf = to_geodataframe(raw_df)
    gdf_with_prox = calculate_station_proximity(gdf)
    df = pd.DataFrame(gdf_with_prox.drop(columns=["geometry"], errors="ignore"))
    risk_df = compute_sector_risk_index(df)
    return df, risk_df


# Load primary dataset anchored to current calendar date
today_str = datetime.now().strftime("%Y-%m-%d")
display_refresh_str = datetime.now().strftime("%d %b %Y")
df, risk_df = load_bhopal_data(num_samples=520, random_seed=101, date_str=today_str)

# Generate Material Active HTML with data connections & daily refresh badge
html_content = generate_material_active_html(df, risk_df, refresh_date=display_refresh_str)

# Sync standalone index.html for direct browser access
try:
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
except Exception:
    pass

# Render the Bhopal Safety Intelligence UI inside Streamlit
components.html(html_content, height=2150, scrolling=True)
