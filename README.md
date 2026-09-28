# 🛡️ Bhopal City-Wide Crime & Safety Mapping Dashboard

An interactive, geospatial civic intelligence platform built with **Streamlit**, **Pandas**, **GeoPandas**, and **Folium**, designed to map, analyze, and visualize crime distribution, safety patterns, and police proximity across Bhopal, Madhya Pradesh.

---

## 🌟 Key Features

1. **Interactive Dual-Mode Folium Map**:
   - **Marker Cluster View**: Color-coded markers mapped across four key Indian Penal Code / BNS crime categories with rich HTML popups (showing offense details, time of day, severity level, status, and proximity to nearest police station).
   - **Kernel Density Heatmap View**: Continuous severity-weighted heat surface highlighting high-density crime corridors and hotspots in Bhopal.
   - **Infrastructure Overlays**: Bhopal Police Stations (Thanas), Mahila Thana (Women's Helpline Hub), and Smart City well-lit safe corridors.

2. **Multi-Parametric Sidebar Filters**:
   - Crime Category selection:
     1. Property Crime & Theft
     2. Assault & Physical Offenses
     3. Public Harassment / Women's Safety
     4. Vandalism / Petty Mischief
   - Time of Day (All Day, Daytime, Nighttime/Post-10 PM).
   - Bhopal Neighborhood / Sector dropdown (MP Nagar, TT Nagar, Old Bhopal/Ibrahimganj, Arera Colony, Shahpura, Kolar Road, Bittan Market, Ayodhya Bypass, Hoshangabad Road).
   - Severity Score Range (1 to 5) and Date Range filter.
   - Quick preset buttons (`Night Focus`, `High Risk`, `Women Safety`, `Reset`).

3. **Risk Analytics & Visualizations**:
   - Top KPI metric cards: Total incidents, dominant crime category, highest-risk sector, and average severity.
   - Interactive Plotly breakdown of crime categories across sectors.
   - Daytime vs Nighttime ratio charts and severity distributions.
   - Neighborhood Safety Index table with automatic risk grading.
   - Law enforcement proximity analysis using metric projections (**EPSG:32643 - UTM Zone 43N**).

4. **Production Open Data Ingestion Blueprint**:
   - Technical guide and code samples for integrating with the **Madhya Pradesh Police Portal** (`bhopal.mppolice.gov.in`), CCTNS e-FIR feeds, and SCRB open records.
   - Integration patterns with **OpenStreetMap** (via `OSMnx` and `Geopy`) to query street lamps, police stations, and pedestrian walkability graphs.
   - DPDP Act compliant privacy protection strategies (spatial jittering, geohash truncation).

---

## 🚀 Quickstart Guide

### 1. Set Up Environment & Install Dependencies
```bash
cd /Users/shreyshrivastava/.gemini/antigravity-ide/scratch/bhopal-crime-safety-dashboard
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📂 Project Structure
```
bhopal-crime-safety-dashboard/
├── app.py                 # Main Streamlit application & layout
├── data_generator.py      # Statistical synthetic crime generator for Bhopal
├── spatial_analytics.py   # GeoPandas proximity calculations & Sector Risk scoring
├── map_builder.py         # Folium multi-layer map rendering engine
├── sourcing_guide.py      # Production data ingestion guide (SCRB, CCTNS, OSMnx)
├── requirements.txt       # Project dependencies
└── README.md              # Documentation
```
