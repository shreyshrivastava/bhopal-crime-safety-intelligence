# 🛡️ Bhopal Safety Intelligence

An interactive, geospatial civic safety intelligence platform built with **Leaflet.js**, **Streamlit**, **Pandas**, and **GeoPandas**, designed to map, analyze, and visualize recorded crime patterns, safety corridors, and station proximity across Bhopal, Madhya Pradesh.

![Bhopal Safety Intelligence Preview](preview.png)

---

## 🌟 Key Features

1. **Interactive Material Active Geospatial Map**:
   - **Marker Cluster View**: Color-coded markers mapped across four key crime categories with rich popups showing incident details, sector, offense subtype, time of day, severity level, and distance to nearest safety post.
   - **Kernel Density Heatmap View**: Continuous severity-weighted heat surface highlighting recorded crime corridors and density hotspots in Bhopal.
   - **Infrastructure Overlays**: Bhopal Police Stations & Helplines (10 Thanas), Mahila Thana (Women's Helpline Hub), and Smart City Safe Corridors.

2. **Connected Search & Filter System**:
   - **Global Search Function**: Real-time keyword filter across sectors, incident IDs, crime categories, and offense subtypes with instant sector zoom/fly-to and clear button.
   - **Quick Ward Selector**: Direct dropdown navigation across all 9 primary Bhopal zones (MP Nagar, TT Nagar, Old Bhopal, Shahpura, Arera Colony, Kolar Road, Bittan Market, Ayodhya Bypass, Hoshangabad Road).
   - **Analyze Filters Action**: Dedicated button that computes multi-parametric filters, refreshes the map, and smoothly transitions into deep statistical analytics.
   - **Incident Filters**: Category selector, Time of Day (All Day, Daytime, Nighttime/Post-10 PM), and Severity slider (Lv 1+ to Lv 5).

3. **Multidimensional Risk Analytics & Tables**:
   - **KPI Metric Overview**: Filtered incident count, dominant crime type percentage, highest-density sector, and average severity rating.
   - **Interactive Charts**: Crime prevalence by sector bar charts, daytime vs. nighttime chrono-bias gauge, severity distribution, and offense modality breakdowns.
   - **Sector Safety & Proximity Ranking**: Composite safety evaluations with geodesic distance calculations to safety posts.
   - **Filtered Crime Records Explorer**: Tabular data inspector with instant search and CSV export.

4. **Floating Capsule Navigation Dock**:
   - Direct, smooth navigation links for **Map**, **Analyze**, **Hotspots**, **Records**, and **Dial 112 SOS**.

---

## 🚀 Quickstart Guide

### 1. Set Up Environment & Install Dependencies
```bash
cd bhopal-crime-safety-dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

Or open `index.html` directly in any modern browser for standalone access!

---

## 📂 Project Structure
```
bhopal-crime-safety-dashboard/
├── app.py                 # Streamlit entry point serving the Material Active UI
├── ui_builder.py          # Material Active UI engine & connected Leaflet template
├── data_generator.py      # Statistical synthetic crime generator for Bhopal
├── spatial_analytics.py   # Vectorized Haversine distance & sector safety index
├── map_builder.py         # Folium multi-layer builder
├── sourcing_guide.py      # Open data pipeline documentation
├── index.html             # Standalone cross-platform distribution file
├── preview.png            # Visual dashboard preview
├── requirements.txt       # Python dependencies
└── Dockerfile             # Containerized deployment manifest
```

---

## 📄 License
MIT License. Created for civic safety research and geospatial intelligence in Bhopal.
