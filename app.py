"""
================================================================================
Bhopal City-Wide Crime and Safety Mapping Dashboard
================================================================================
A full-stack geospatial intelligence and civic safety application built with
Streamlit, Pandas, GeoPandas, Folium, and Plotly.

Target Geography: Bhopal, Madhya Pradesh, India (Lat: 23.2599° N, Lon: 77.4126° E)
Key Sectors: MP Nagar, TT Nagar, Old Bhopal/Ibrahimganj, Arera Colony, Shahpura,
             Kolar Road, Bittan Market, Ayodhya Bypass, Hoshangabad Road.

PRODUCTION DATA INTEGRATION NOTICE:
-----------------------------------
This application is configured with simulated yet statistically calibrated crime data
modeled directly on Bhopal urban dynamics. To connect live official crime feeds:
1. Query the Madhya Pradesh Police Citizen Portal (https://bhopal.mppolice.gov.in/fir-status/)
   or CCTNS e-FIR XML/JSON feeds to ingest registered First Information Reports.
2. Interrogate the State Crime Records Bureau (SCRB) annual datasets via data.gov.in.
3. Use OSMnx (`ox.geometries_from_place("Bhopal, MP", tags={'amenity': 'police'})`)
   and Geopy to pull real police station coordinates, street lighting, and CCTV nodes.
See the dedicated 'Production Sourcing Guide' tab in this app for complete code.
================================================================================
"""

# ==============================================================================
# 1. CORE DEPENDENCY IMPORTS
# ==============================================================================
import os
# Ensure macOS ARM64 / Apple Silicon fork safety for multithreaded servers
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["PROJ_NETWORK"] = "OFF"

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# Import domain modules from local project package
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
from map_builder import (
    build_bhopal_map,
    CATEGORY_PALETTE
)
from sourcing_guide import GUIDE_MARKDOWN

# ==============================================================================
# 2. STREAMLIT PAGE CONFIGURATION & CUSTOM AESTHETICS
# ==============================================================================
st.set_page_config(
    page_title="Bhopal Crime & Safety Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Aesthetic Styling (Glassmorphism, Clean Cards, Responsive Typography)
CUSTOM_CSS = """
<style>
    /* Global Typography & Palette */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Metric Card Styling */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.9));
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 4px 14px -2px rgba(15, 23, 42, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px -3px rgba(15, 23, 42, 0.10);
    }
    .metric-card-accent {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
    }
    .metric-title {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
    .metric-subtitle {
        font-size: 0.80rem;
        color: #94A3B8;
        margin-top: 6px;
        font-weight: 500;
    }

    /* Header Banner Styling */
    .dashboard-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F2847 100%);
        color: #FFFFFF;
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
    }
    .dashboard-tagline {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-top: 4px;
    }
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.18);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34D399;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10B981;
    }

    /* Custom Category Badges */
    .badge-property {
        background-color: #FFF7ED;
        color: #C2410C;
        border: 1px solid #FDBA74;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-assault {
        background-color: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FCA5A5;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-harassment {
        background-color: #FAF5FF;
        color: #7E22CE;
        border: 1px solid #D8B4FE;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-vandalism {
        background-color: #FEFCE8;
        color: #A16207;
        border: 1px solid #FDE047;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.78rem;
    }

    /* Streamlit overrides */
    div[data-testid="stMetricValue"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# 3. DATA INGESTION & CACHING PIPELINE
# ==============================================================================
@st.cache_data(show_spinner=False)
def load_bhopal_crime_data(num_samples: int = 500, random_seed: int = 42) -> pd.DataFrame:
    """
    Loads and caches the structured Bhopal crime dataset.
    Performs spatial proximity calculations to nearest police stations using GeoPandas.
    """
    df = generate_crime_dataset(n_samples=num_samples, seed=random_seed)
    gdf = to_geodataframe(df)
    
    # Calculate proximity to nearest Bhopal Police Station via projected CRS (EPSG:32643 - UTM 43N)
    gdf_with_proximity = calculate_station_proximity(gdf)
    
    # Return as standard DataFrame with geometry attributes preserved
    result_df = pd.DataFrame(gdf_with_proximity.drop(columns=["geometry"], errors="ignore"))
    return result_df


# Load primary dataset
raw_df = load_bhopal_crime_data(num_samples=520, random_seed=101)


# ==============================================================================
# 4. SIDEBAR CONFIGURATION & MULTI-PARAMETRIC FILTERS
# ==============================================================================
with st.sidebar:
    st.markdown("### 🛡️ Bhopal Safety Filters")
    st.caption("City-wide geospatial control center • MP Police Jurisdiction")
    
    # Quick Preset Buttons
    st.markdown("**⚡ Quick Analysis Presets**")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        if st.button("🌙 Night Focus", use_container_width=True, help="Filters incidents occurring post-10 PM"):
            st.session_state["time_filter"] = "Nighttime/Post-10 PM"
        if st.button("🚨 High Risk", use_container_width=True, help="Severity 4 and 5 incidents"):
            st.session_state["min_severity"] = 4
    with p_col2:
        if st.button("👩 Women Safety", use_container_width=True, help="Public Harassment focus"):
            st.session_state["cat_filter"] = ["Public Harassment / Women's Safety"]
        if st.button("🔄 Reset Filters", use_container_width=True):
            st.session_state["time_filter"] = "All Day"
            st.session_state["min_severity"] = 1
            st.session_state["cat_filter"] = list(CATEGORY_PALETTE.keys())
            st.session_state["nh_filter"] = "All Bhopal Sectors"

    st.markdown("---")

    # 1. Crime Category Filter (Multi-select)
    all_categories = list(CATEGORY_PALETTE.keys())
    default_cats = st.session_state.get("cat_filter", all_categories)
    selected_categories = st.multiselect(
        "Incident Categories:",
        options=all_categories,
        default=default_cats,
        help="Filter one or multiple Indian Penal Code / BNS crime clusters"
    )

    # 2. Time of Day Filter
    time_options = ["All Day", "Daytime", "Nighttime/Post-10 PM"]
    default_time_idx = time_options.index(st.session_state.get("time_filter", "All Day"))
    selected_time = st.selectbox(
        "Time of Day:",
        options=time_options,
        index=default_time_idx,
        help="Partition daytime vs night-shift (post 10:00 PM) occurrences"
    )

    # 3. Neighborhood / Zone Selector
    all_neighborhoods = ["All Bhopal Sectors"] + sorted(list(NEIGHBORHOOD_CONFIG.keys()))
    default_nh = st.session_state.get("nh_filter", "All Bhopal Sectors")
    default_nh_idx = all_neighborhoods.index(default_nh) if default_nh in all_neighborhoods else 0
    selected_neighborhood = st.selectbox(
        "Bhopal Neighborhood / Zone:",
        options=all_neighborhoods,
        index=default_nh_idx,
        help="Isolate analysis to a specific sector or inspect entire city"
    )

    # 4. Severity Score Range
    min_sev_default = int(st.session_state.get("min_severity", 1))
    severity_range = st.slider(
        "Severity Score Range (1=Minor to 5=Critical):",
        min_value=1,
        max_value=5,
        value=(min_sev_default, 5),
        step=1
    )

    # 5. Date Range Selector
    min_date = raw_df["date"].min()
    max_date = raw_df["date"].max()
    selected_date_range = st.date_input(
        "Incident Date Range:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    st.markdown("---")
    st.markdown("### 🗺️ Geospatial Layer Controls")

    # Dual-Mode Map Toggle (Required Feature)
    map_view_mode = st.radio(
        "Visualization Mode:",
        options=["Marker Cluster", "Kernel Density Heatmap"],
        index=0,
        help="Switch between individual color-coded markers or continuous density heatmap"
    )

    # Secondary Layer Toggles
    show_police = st.checkbox("Show Police Stations (Thanas & Helplines)", value=True)
    show_corridors = st.checkbox("Show Smart City Safe Corridors", value=True)

    # Map Rendering Engine Option
    map_engine = st.selectbox(
        "Map Render Engine:",
        options=["Native Leaflet (Fast, 100% Reliable)", "Streamlit-Folium Component"],
        index=0,
        help="Native Leaflet embeds the complete Folium map directly, bypassing browser extension/Brave shield blocks."
    )

    st.markdown("---")
    st.caption("Bhopal Smart City Development Corp (BSCDCL) & MP Police Integration Node.")


# ==============================================================================
# 5. DATA FILTERING ENGINE
# ==============================================================================
filtered_df = raw_df.copy()

# Filter by Category
if selected_categories:
    filtered_df = filtered_df[filtered_df["crime_category"].isin(selected_categories)]
else:
    filtered_df = filtered_df.iloc[0:0]

# Filter by Time of Day
if selected_time != "All Day":
    filtered_df = filtered_df[filtered_df["time_of_day"] == selected_time]

# Filter by Neighborhood
if selected_neighborhood != "All Bhopal Sectors":
    filtered_df = filtered_df[filtered_df["neighborhood"] == selected_neighborhood]

# Filter by Severity
filtered_df = filtered_df[
    (filtered_df["severity_score"] >= severity_range[0]) & 
    (filtered_df["severity_score"] <= severity_range[1])
]

# Filter by Date Range
if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_d, end_d = selected_date_range
    filtered_df = filtered_df[(filtered_df["date"] >= start_d) & (filtered_df["date"] <= end_d)]


# ==============================================================================
# 6. HEADER & METRIC KPI DASHBOARD
# ==============================================================================
# Top Header Banner
st.markdown(
    """
    <div class="dashboard-header">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
            <div>
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                    <h1 style="margin:0; font-size:1.85rem; font-weight:800; letter-spacing:-0.02em;">
                        Bhopal City Crime & Safety Intelligence Portal
                    </h1>
                    <span class="live-badge">
                        <span class="pulse-dot"></span> Active Feed
                    </span>
                </div>
                <div class="dashboard-tagline">
                    Geospatial risk mapping, law enforcement proximity, and predictive urban safety telemetry for Bhopal, MP.
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.75rem; color:#94A3B8; text-transform:uppercase; letter-spacing:0.06em; font-weight:600;">
                    Emergency Response
                </div>
                <div style="font-size:1.25rem; font-weight:800; color:#38BDF8;">
                    Dial 112 / 1090 (Women)
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Metric Calculations
total_incidents = len(filtered_df)
if total_incidents > 0:
    peak_category = filtered_df["crime_category"].mode()[0]
    peak_cat_count = (filtered_df["crime_category"] == peak_category).sum()
    peak_cat_pct = round((peak_cat_count / total_incidents) * 100, 1)

    peak_zone = filtered_df["neighborhood"].mode()[0]
    peak_zone_count = (filtered_df["neighborhood"] == peak_zone).sum()
    
    avg_severity = round(filtered_df["severity_score"].mean(), 2)
    high_sev_count = (filtered_df["severity_score"] >= 4).sum()
    high_sev_pct = round((high_sev_count / total_incidents) * 100, 1)
else:
    peak_category = "No Data"
    peak_cat_pct = 0.0
    peak_zone = "N/A"
    peak_zone_count = 0
    avg_severity = 0.0
    high_sev_pct = 0.0

# Render 4 Premium KPI Metric Cards
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-card-accent" style="background:#3B82F6;"></div>
            <div class="metric-title">Filtered Incidents</div>
            <div class="metric-value">{total_incidents:,}</div>
            <div class="metric-subtitle">Out of {len(raw_df)} total recorded in period</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with kpi_col2:
    badge_style = "color:#FF7A00;"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-card-accent" style="background:#FF7A00;"></div>
            <div class="metric-title">Dominant Crime Type</div>
            <div class="metric-value" style="font-size:1.35rem; line-height:1.3; color:#C2410C;">
                {peak_category}
            </div>
            <div class="metric-subtitle">{peak_cat_pct}% of filtered offenses ({peak_cat_count} cases)</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with kpi_col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-card-accent" style="background:#EF4444;"></div>
            <div class="metric-title">Highest-Risk Sector</div>
            <div class="metric-value" style="font-size:1.35rem; line-height:1.3; color:#DC2626;">
                {peak_zone}
            </div>
            <div class="metric-subtitle">{peak_zone_count} reported events in selected sector</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with kpi_col4:
    sev_color = "#10B981" if avg_severity < 2.5 else "#F59E0B" if avg_severity < 3.8 else "#EF4444"
    sev_label = "Low" if avg_severity < 2.5 else "Moderate" if avg_severity < 3.8 else "Elevated"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-card-accent" style="background:{sev_color};"></div>
            <div class="metric-title">Average Severity</div>
            <div class="metric-value" style="color:{sev_color};">
                {avg_severity} <span style="font-size:1rem; font-weight:600; color:#64748B;">/ 5.0</span>
            </div>
            <div class="metric-subtitle">Rating: <b>{sev_label}</b> ({high_sev_pct}% rated High/Critical)</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# 7. INTERACTIVE GEOSPATIAL MAP VIEW (FOLIUM + STREAMLIT-FOLIUM)
# ==============================================================================
st.markdown("### 🗺️ Interactive Geospatial Incident & Safety Map")

if filtered_df.empty:
    st.warning("⚠️ No incidents match the selected filter criteria. Please adjust your sidebar settings.")
else:
    # Top Map Status & Legend Bar
    legend_cols = st.columns([4, 1])
    with legend_cols[0]:
        st.markdown(
            """
            <div style="display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin-bottom:8px; font-size:0.85rem;">
                <b>Category Legend:</b>
                <span class="badge-property">🟠 Property Crime & Theft</span>
                <span class="badge-assault">🔴 Assault & Physical</span>
                <span class="badge-harassment">🟣 Women's Safety / Harassment</span>
                <span class="badge-vandalism">🟡 Vandalism & Mischief</span>
                <span style="color:#0284C7; font-weight:600;">🔷 Police Thana</span>
                <span style="color:#0EA5E9; font-weight:600;">── Safe Corridor</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with legend_cols[1]:
        mode_badge = "📍 Marker Cluster" if map_view_mode == "Marker Cluster" else "🔥 Kernel Heatmap"
        st.markdown(
            f"<div style='text-align:right; font-weight:700; color:#475569; font-size:0.85rem;'>Mode: <span style='color:#2563EB;'>{mode_badge}</span></div>",
            unsafe_allow_html=True
        )

    # Build Folium Map
    bhopal_map = build_bhopal_map(
        filtered_df=filtered_df,
        view_mode=map_view_mode,
        show_police_stations=show_police,
        show_safe_corridors=show_corridors,
        selected_neighborhood=selected_neighborhood
    )

    # Render Folium Map using selected engine
    if map_engine == "Streamlit-Folium Component":
        try:
            st_folium(
                bhopal_map,
                use_container_width=True,
                height=560,
                returned_objects=[]
            )
        except Exception:
            components.html(bhopal_map._repr_html_(), height=560, scrolling=False)
    else:
        # Native Leaflet direct HTML render - fast, smooth, zero websocket overhead
        components.html(bhopal_map._repr_html_(), height=560, scrolling=False)

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# 8. RISK ANALYTICS & STATISTICAL BREAKDOWN SECTION
# ==============================================================================
tab_analytics, tab_sectors, tab_data, tab_sourcing = st.tabs([
    "📊 Risk Analytics & Trends",
    "🏘️ Sector Safety & Proximity Ranking",
    "📋 Filtered Records Explorer",
    "🏛️ Production Sourcing Guide (Open Data / OSMnx)"
])

# ------------------------------------------------------------------------------
# TAB 1: RISK ANALYTICS & PLOTLY VISUALIZATIONS
# ------------------------------------------------------------------------------
with tab_analytics:
    st.markdown("#### 📈 Multidimensional Crime Patterns Across Bhopal Sectors")
    
    chart_col1, chart_col2 = st.columns([1.6, 1])

    with chart_col1:
        # 1. Sector vs Crime Category Stacked Breakdown
        if not filtered_df.empty:
            sector_cat_counts = (
                filtered_df.groupby(["neighborhood", "crime_category"])
                .size()
                .reset_index(name="incident_count")
            )
            
            # Palette mapping for Plotly
            color_discrete_map = {
                "Property Crime & Theft": "#FF7A00",
                "Assault & Physical Offenses": "#E63946",
                "Public Harassment / Women's Safety": "#9333EA",
                "Vandalism / Petty Mischief": "#EAB308"
            }

            fig_sector = px.bar(
                sector_cat_counts,
                x="incident_count",
                y="neighborhood",
                color="crime_category",
                orientation="h",
                title="<b>Crime Category Prevalence by Bhopal Sector</b>",
                color_discrete_map=color_discrete_map,
                labels={"incident_count": "Reported Incidents", "neighborhood": "Sector / Zone", "crime_category": "Category"},
                text_auto=True
            )
            fig_sector.update_layout(
                barmode="stack",
                yaxis={'categoryorder': 'total ascending'},
                margin=dict(l=10, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif")
            )
            fig_sector.update_xaxes(showgrid=True, gridcolor="#E2E8F0")
            st.plotly_chart(fig_sector, use_container_width=True)
        else:
            st.info("No data available to plot.")

    with chart_col2:
        # 2. Daytime vs Nighttime Hourly Distribution
        if not filtered_df.empty:
            time_df = filtered_df.groupby("time_of_day").size().reset_index(name="count")
            
            fig_pie = px.pie(
                time_df,
                names="time_of_day",
                values="count",
                title="<b>Daytime vs. Nighttime Distribution</b>",
                color="time_of_day",
                color_discrete_map={
                    "Daytime": "#0284C7",
                    "Nighttime/Post-10 PM": "#6366F1"
                },
                hole=0.55
            )
            fig_pie.update_layout(
                margin=dict(l=10, r=10, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif")
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No data available to plot.")

    # 3. Severity Distribution & Subtype Drill-Down
    drill_col1, drill_col2 = st.columns(2)
    with drill_col1:
        if not filtered_df.empty:
            sev_counts = filtered_df["severity_score"].value_counts().sort_index().reset_index()
            sev_counts.columns = ["severity_score", "count"]
            sev_counts["severity_label"] = [f"Level {s} ({'Minor' if s==1 else 'Low' if s==2 else 'Moderate' if s==3 else 'High' if s==4 else 'Critical'})" for s in sev_counts["severity_score"]]

            fig_sev = px.bar(
                sev_counts,
                x="severity_label",
                y="count",
                title="<b>Incidents by Severity Level (1 to 5)</b>",
                color="severity_score",
                color_continuous_scale=["#10B981", "#84CC16", "#F59E0B", "#F97316", "#EF4444"],
                labels={"count": "Number of Incidents", "severity_label": "Severity Scale"}
            )
            fig_sev.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=40, b=20),
                coloraxis_showscale=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif")
            )
            fig_sev.update_yaxes(showgrid=True, gridcolor="#E2E8F0")
            st.plotly_chart(fig_sev, use_container_width=True)

    with drill_col2:
        if not filtered_df.empty:
            top_subtypes = filtered_df["crime_subtype"].value_counts().head(7).reset_index()
            top_subtypes.columns = ["subtype", "count"]

            fig_sub = px.bar(
                top_subtypes,
                x="count",
                y="subtype",
                orientation="h",
                title="<b>Most Frequent Offense Modalities</b>",
                color_discrete_sequence=["#3B82F6"],
                labels={"count": "Incident Count", "subtype": "Offense Type"}
            )
            fig_sub.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=300,
                margin=dict(l=10, r=10, t=40, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif")
            )
            fig_sub.update_xaxes(showgrid=True, gridcolor="#E2E8F0")
            st.plotly_chart(fig_sub, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 2: SECTOR SAFETY & PROXIMITY RANKING (GEOPANDAS PROJECTIONS)
# ------------------------------------------------------------------------------
with tab_sectors:
    st.markdown("#### 🏘️ Bhopal Neighborhood Safety Index & Law Enforcement Coverage")
    st.caption("Composite risk calculations computed using spatial aggregation and projected distance metrics (EPSG:32643 UTM Zone 43N).")
    
    sector_summary_df = compute_sector_risk_index(filtered_df)
    
    if not sector_summary_df.empty:
        # Display Sector Summary Table with native visual bars and indicators
        disp_cols = ["Neighborhood", "Incidents", "Avg Severity", "High Severity Count", "Nighttime Ratio (%)", "Dominant Crime", "Risk Score", "Risk Level"]
        
        column_configuration = {
            "Risk Score": st.column_config.ProgressColumn(
                "Risk Index (0-100)",
                help="Composite neighborhood risk index based on volume, severity, and night ratio",
                format="%.1f",
                min_value=0,
                max_value=100
            ),
            "Nighttime Ratio (%)": st.column_config.ProgressColumn(
                "Nighttime Ratio",
                help="Proportion of offenses occurring post-10 PM",
                format="%.1f%%",
                min_value=0,
                max_value=100
            ),
            "Avg Severity": st.column_config.NumberColumn(
                "Avg Severity",
                help="Average severity on 1 to 5 scale",
                format="%.2f / 5.0"
            ),
            "Incidents": st.column_config.NumberColumn(
                "Incidents",
                format="%d cases"
            )
        }

        try:
            # If matplotlib is available, optionally apply background highlight or directly render styled dataframe
            st.dataframe(
                sector_summary_df[disp_cols],
                column_config=column_configuration,
                use_container_width=True,
                height=340
            )
        except Exception:
            st.dataframe(
                sector_summary_df[disp_cols],
                use_container_width=True,
                height=340
            )

        st.markdown("##### 📍 Law Enforcement Proximity Analysis")
        prox_col1, prox_col2 = st.columns([1, 1])
        
        with prox_col1:
            avg_dist = filtered_df["distance_to_station_km"].mean()
            max_dist = filtered_df["distance_to_station_km"].max()
            min_dist = filtered_df["distance_to_station_km"].min()
            
            st.info(
                f"""
                **Police Proximity Highlights for Current Filter:**
                - **Average Distance to Nearest Thana:** `{avg_dist:.2f} km`
                - **Closest Incident to Station:** `{min_dist:.2f} km`
                - **Furthest Incident from Station:** `{max_dist:.2f} km`
                
                *Incidents with > 2.5 km distance to the nearest police post are prioritized for mobile dial-112 PCR van patrols.*
                """
            )
            
        with prox_col2:
            # Breakdown of coverage by Police Station
            ps_coverage = filtered_df["nearest_station"].value_counts().head(6).reset_index()
            ps_coverage.columns = ["Police Station", "Jurisdiction Incidents"]
            
            fig_ps = px.bar(
                ps_coverage,
                x="Jurisdiction Incidents",
                y="Police Station",
                orientation="h",
                title="<b>Caseload by Primary Responsive Thana</b>",
                color_discrete_sequence=["#0284C7"]
            )
            fig_ps.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=230,
                margin=dict(l=10, r=10, t=35, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif")
            )
            st.plotly_chart(fig_ps, use_container_width=True)
    else:
        st.info("No data in current filter to calculate sector rankings.")


# ------------------------------------------------------------------------------
# TAB 3: FILTERED RECORDS EXPLORER & CSV EXPORT
# ------------------------------------------------------------------------------
with tab_data:
    st.markdown("#### 📋 Incident Registry Explorer")
    st.caption("Search, inspect, and export the filtered incidents dataset.")
    
    # Search Box
    search_query = st.text_input("🔍 Search Incident ID, Offense Subtype, or Neighborhood:", "")
    
    table_df = filtered_df.copy()
    if search_query:
        mask = (
            table_df["incident_id"].str.contains(search_query, case=False, na=False) |
            table_df["neighborhood"].str.contains(search_query, case=False, na=False) |
            table_df["crime_subtype"].str.contains(search_query, case=False, na=False) |
            table_df["status"].str.contains(search_query, case=False, na=False)
        )
        table_df = table_df[mask]

    view_columns = [
        "incident_id", "date", "time_of_day", "neighborhood", 
        "crime_category", "crime_subtype", "severity_score", 
        "nearest_station", "distance_to_station_km", "status"
    ]
    
    st.dataframe(
        table_df[view_columns],
        use_container_width=True,
        height=400
    )

    # Download CSV Action
    csv_bytes = table_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Crime Registry (CSV)",
        data=csv_bytes,
        file_name=f"bhopal_crime_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        help="Export data for further statistical analysis or GIS software"
    )


# ------------------------------------------------------------------------------
# TAB 4: PRODUCTION SOURCING GUIDE & OPEN-DATA PIPELINE
# ------------------------------------------------------------------------------
with tab_sourcing:
    st.markdown(GUIDE_MARKDOWN)

# ==============================================================================
# 9. FOOTER
# ==============================================================================
st.markdown("---")
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.80rem; color:#64748B;">
        <div>
            <b>Bhopal Crime & Safety Intelligence Dashboard</b> • Built with Streamlit, Folium, GeoPandas & Plotly
        </div>
        <div>
            Madhya Pradesh Open Data • Police Commissionerate Bhopal
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
