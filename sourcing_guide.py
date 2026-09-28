"""
Bhopal Crime & Safety Intelligence Dashboard
Production Data Ingestion & Investigation Guide
Reference implementation and architectural blueprint for swapping mock data with live open data.
"""

GUIDE_MARKDOWN = """
## 🏛️ Real-World Data Investigation & Sourcing Blueprint

This dashboard currently uses a calibrated spatial simulation modeled after real Bhopal neighborhoods. 
To transition this prototype into a live civic intelligence platform, follow this technical blueprint.

---

### 1. Official Law Enforcement Portals & Public Registers

#### A. Madhya Pradesh Police Citizen Portal (CCTNS / e-FIR)
- **Primary Portal:** [Bhopal Police Commissionerate / MP Police Portal](https://bhopal.mppolice.gov.in/fir-status/)
- **Data Attributes Available:**
  - FIR Number (`fir_no`) & Registration Date (`reg_date`)
  - Police Station Jurisdiction (`ps_id`, e.g., MP Nagar Thana, TT Nagar Thana)
  - Indian Penal Code (IPC) / Bharatiya Nyaya Sanhita (BNS) offense sections:
    - *Theft / Snatching:* IPC 379, 392 (BNS 303, 309)
    - *Assault / Hurt:* IPC 323, 324, 307 (BNS 115, 117, 109)
    - *Harassment & Women Safety:* IPC 354, 354D, 509 (BNS 74, 78, 79)
    - *Mischief / Vandalism:* IPC 427, 435 (BNS 324)
  - Incident Status: Under Investigation, Chargesheeted, Final Report (FR) Filed.

#### B. State Crime Records Bureau (SCRB) & NCRB Open Data
- **Annual / Monthly Compendiums:** Open Government Data (OGD) Platform India ([data.gov.in](https://data.gov.in))
- **Madhya Pradesh SCRB:** Publishes aggregate district-level crime statistics for Bhopal Urban and Bhopal Rural commissionerates.
- **Ingestion Pipeline Pattern:**
  ```python
  # ETL Example: Transforming official CCTNS JSON exports
  def parse_cctns_fir_feed(raw_json_stream):
      records = []
      for entry in raw_json_stream["fir_list"]:
          records.append({
              "incident_id": f"BHP-FIR-{entry['fir_no']}-{entry['year']}",
              "police_station": entry["ps_name"],
              "bns_sections": entry["sections"],
              "category": map_bns_to_dashboard_category(entry["sections"]),
              "date": entry["occurrence_date"],
              "time_of_day": "Nighttime/Post-10 PM" if entry["hour"] >= 22 or entry["hour"] < 5 else "Daytime",
              # Coordinates obtained via Geocoding incident landmark
              "latitude": entry.get("resolved_lat"),
              "longitude": entry.get("resolved_lon")
          })
      return pd.DataFrame(records)
  ```

---

### 2. OpenStreetMap (OSM) Ingestion via OSMnx & Geopy

To automatically retrieve real Bhopal police stations, street lamps, and road nodes:

```python
import osmnx as ox
import geopandas as gpd

def fetch_bhopal_police_infrastructure():
    '''
    Pulls live Police Station (amenity=police) geometries from OSM within Bhopal.
    '''
    place_name = "Bhopal, Madhya Pradesh, India"
    tags = {"amenity": "police"}
    
    # Download OSM points of interest
    police_gdf = ox.geometries_from_place(place_name, tags=tags)
    
    # Standardize output columns
    stations = []
    for idx, row in police_gdf.iterrows():
        point = row.geometry.centroid if row.geometry.geom_type != "Point" else row.geometry
        stations.append({
            "name": row.get("name", "Bhopal Police Post"),
            "lat": point.y,
            "lon": point.x,
            "phone": row.get("phone", "112 / 0755-2555500"),
            "jurisdiction": row.get("addr:district", "Bhopal Urban")
        })
    return gpd.GeoDataFrame(stations)

def fetch_bhopal_lighting_and_surveillance():
    '''
    Queries OSM for smart city street lighting (highway=street_lamp or lit=yes)
    to calculate safe pedestrian corridor metrics.
    '''
    bhopal_graph = ox.graph_from_place("Bhopal, MP, India", network_type="walk")
    nodes, edges = ox.graph_to_gdfs(bhopal_graph)
    lit_corridors = edges[edges["lit"] == "yes"]
    return lit_corridors
```

---

### 3. Geocoding Landmark Names to Exact Coordinates (Nominatim / Geopy)

```python
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

def geocode_bhopal_incident_address(address_string: str):
    '''
    Resolves local Bhopal landmark strings (e.g. 'Near Jyoti Cinema, MP Nagar Zone 1')
    to accurate latitude and longitude coordinates.
    '''
    geolocator = Nominatim(user_agent="bhopal_safety_intelligence_v1")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    
    query = f"{address_string}, Bhopal, Madhya Pradesh, India"
    location = geocode(query)
    if location:
        return location.latitude, location.longitude
    return 23.2500, 77.4170 # Fallback Bhopal centroid
```

---

### 4. Ethical Privacy, Anonymization & Geofencing (DPDP Compliance)

> [!IMPORTANT]
> **Data Privacy & Protection Rules:**
> 1. **Spatial Jittering / Offset:** Never publish pinpoint coordinates of residential burglaries or sexual harassment incidents. Apply a random Gaussian displacement ($r \\sim \\mathcal{N}(0, 75\\text{ meters})$) or aggregate to the neighborhood centroid.
> 2. **Geohashing:** Truncate coordinates to Geohash Precision 6 or 7 (~150m cell size).
> 3. **PII Redaction:** Automatically strip victim and informant names, exact house numbers, and vehicular registration plates from public dashboards.
"""

if __name__ == "__main__":
    print(GUIDE_MARKDOWN[:300])
