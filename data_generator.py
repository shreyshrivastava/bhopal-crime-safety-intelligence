"""
Bhopal Crime & Safety Intelligence Dashboard
Synthetic Data Generator Engine
Simulates realistic crime, temporal patterns, and geographic points across Bhopal, MP.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime, timedelta

# Realistic neighborhood centroids and baseline characteristics in Bhopal
NEIGHBORHOOD_CONFIG = {
    "MP Nagar": {
        "lat": 23.2329,
        "lon": 77.4338,
        "spread": 0.006,
        "base_weight": 0.18,
        "crime_prop": {
            "Property Crime & Theft": 0.50,
            "Assault & Physical Offenses": 0.15,
            "Public Harassment / Women's Safety": 0.20,
            "Vandalism / Petty Mischief": 0.15,
        },
        "night_bias": 0.40,
        "zone_type": "Commercial & Transit Hub"
    },
    "TT Nagar / New Market": {
        "lat": 23.2313,
        "lon": 77.4010,
        "spread": 0.005,
        "base_weight": 0.15,
        "crime_prop": {
            "Property Crime & Theft": 0.42,
            "Assault & Physical Offenses": 0.18,
            "Public Harassment / Women's Safety": 0.25,
            "Vandalism / Petty Mischief": 0.15,
        },
        "night_bias": 0.35,
        "zone_type": "Retail & Civic Center"
    },
    "Old Bhopal / Ibrahimganj": {
        "lat": 23.2680,
        "lon": 77.4085,
        "spread": 0.006,
        "base_weight": 0.16,
        "crime_prop": {
            "Property Crime & Theft": 0.35,
            "Assault & Physical Offenses": 0.28,
            "Public Harassment / Women's Safety": 0.22,
            "Vandalism / Petty Mischief": 0.15,
        },
        "night_bias": 0.45,
        "zone_type": "Dense Heritage Bazaar"
    },
    "Arera Colony": {
        "lat": 23.2085,
        "lon": 77.4335,
        "spread": 0.008,
        "base_weight": 0.10,
        "crime_prop": {
            "Property Crime & Theft": 0.55,
            "Assault & Physical Offenses": 0.08,
            "Public Harassment / Women's Safety": 0.15,
            "Vandalism / Petty Mischief": 0.22,
        },
        "night_bias": 0.55,
        "zone_type": "Affluent Residential (Sectors E1-E7)"
    },
    "Shahpura": {
        "lat": 23.1950,
        "lon": 77.4265,
        "spread": 0.007,
        "base_weight": 0.11,
        "crime_prop": {
            "Property Crime & Theft": 0.30,
            "Assault & Physical Offenses": 0.20,
            "Public Harassment / Women's Safety": 0.32,
            "Vandalism / Petty Mischief": 0.18,
        },
        "night_bias": 0.60,
        "zone_type": "Lakefront & Youth Hangout"
    },
    "Kolar Road": {
        "lat": 23.1750,
        "lon": 77.4180,
        "spread": 0.009,
        "base_weight": 0.12,
        "crime_prop": {
            "Property Crime & Theft": 0.45,
            "Assault & Physical Offenses": 0.15,
            "Public Harassment / Women's Safety": 0.18,
            "Vandalism / Petty Mischief": 0.22,
        },
        "night_bias": 0.50,
        "zone_type": "Rapidly Expanding Suburb"
    },
    "Bittan Market": {
        "lat": 23.2155,
        "lon": 77.4290,
        "spread": 0.005,
        "base_weight": 0.08,
        "crime_prop": {
            "Property Crime & Theft": 0.46,
            "Assault & Physical Offenses": 0.12,
            "Public Harassment / Women's Safety": 0.28,
            "Vandalism / Petty Mischief": 0.14,
        },
        "night_bias": 0.30,
        "zone_type": "Weekly Haat & Market Square"
    },
    "Ayodhya Bypass": {
        "lat": 23.2750,
        "lon": 77.4650,
        "spread": 0.008,
        "base_weight": 0.05,
        "crime_prop": {
            "Property Crime & Theft": 0.52,
            "Assault & Physical Offenses": 0.18,
            "Public Harassment / Women's Safety": 0.15,
            "Vandalism / Petty Mischief": 0.15,
        },
        "night_bias": 0.65,
        "zone_type": "Highway Corridor & Freight"
    },
    "Hoshangabad Road": {
        "lat": 23.1780,
        "lon": 77.4520,
        "spread": 0.009,
        "base_weight": 0.05,
        "crime_prop": {
            "Property Crime & Theft": 0.48,
            "Assault & Physical Offenses": 0.16,
            "Public Harassment / Women's Safety": 0.22,
            "Vandalism / Petty Mischief": 0.14,
        },
        "night_bias": 0.50,
        "zone_type": "Commercial Malls & Auto Corridor"
    }
}

CRIME_DETAILS = {
    "Property Crime & Theft": {
        "subtypes": [
            "Two-Wheeler / Bike Theft",
            "Mobile & Gold Chain Snatching",
            "Residential Night Burglary",
            "Commercial Store Shoplifting",
            "Car Stereo & Battery Theft",
            "ATM Cash Counter Tampering"
        ],
        "base_severity": [2, 3, 4],
        "severity_weights": [0.45, 0.40, 0.15]
    },
    "Assault & Physical Offenses": {
        "subtypes": [
            "Street Brawl / Public Altercation",
            "Road Rage Confrontation",
            "Armed Physical Aggression",
            "Commercial Area Dispute",
            "Minor Injury Assault"
        ],
        "base_severity": [3, 4, 5],
        "severity_weights": [0.35, 0.45, 0.20]
    },
    "Public Harassment / Women's Safety": {
        "subtypes": [
            "Stalking / Unsolicited Following",
            "Verbal Catcalling & Eve-teasing",
            "Transit Stop Harassment",
            "Voyeurism & Inappropriate Recording",
            "Aggressive Menacing at Night"
        ],
        "base_severity": [2, 3, 4, 5],
        "severity_weights": [0.30, 0.35, 0.25, 0.10]
    },
    "Vandalism / Petty Mischief": {
        "subtypes": [
            "Park Lighting & Signboard Defacement",
            "Graffiti on Commercial Walls",
            "Vehicle Window Smashing",
            "Public Dustbin & Utility Damage",
            "Rowdy Drunken Conduct in Public"
        ],
        "base_severity": [1, 2, 3],
        "severity_weights": [0.50, 0.35, 0.15]
    }
}

POLICE_STATIONS = [
    {"name": "MP Nagar Police Station", "lat": 23.2355, "lon": 77.4312, "phone": "0755-2555922", "jurisdiction": "Zone-1 Commercial"},
    {"name": "TT Nagar Police Station", "lat": 23.2285, "lon": 77.4035, "phone": "0755-2555920", "jurisdiction": "New Market & Stadium"},
    {"name": "Shahpura Police Station", "lat": 23.1920, "lon": 77.4290, "phone": "0755-2428100", "jurisdiction": "Lakefront & Sector A-C"},
    {"name": "Habibganj Police Station", "lat": 23.2160, "lon": 77.4385, "phone": "0755-2555925", "jurisdiction": "Arera Colony / Station"},
    {"name": "Hanumanganj Thana (Ibrahimganj)", "lat": 23.2655, "lon": 77.4110, "phone": "0755-2533100", "jurisdiction": "Old City Bazaars"},
    {"name": "Kolar Thana", "lat": 23.1680, "lon": 77.4160, "phone": "0755-2490100", "jurisdiction": "Kolar & Sarvdharm"},
    {"name": "Talaiya Police Station", "lat": 23.2560, "lon": 77.4020, "phone": "0755-2542100", "jurisdiction": "Upper Lake & VIP Road"},
    {"name": "Govindpura Police Station", "lat": 23.2550, "lon": 77.4680, "phone": "0755-2586100", "jurisdiction": "Industrial Area BHEL"},
    {"name": "Shyamla Hills Police Station", "lat": 23.2405, "lon": 77.3850, "phone": "0755-2555930", "jurisdiction": "Museums & VIP Zone"},
    {"name": "Mahila Thana (Women's Special Station)", "lat": 23.2475, "lon": 77.4140, "phone": "1090 / 0755-2443801", "jurisdiction": "City-Wide Women Safety Unit"}
]

SAFE_CORRIDORS = [
    {"name": "Smart City VIP Road Corridor", "coords": [[23.2450, 77.3850], [23.2520, 77.3950], [23.2580, 77.4030]], "status": "24/7 CCTV & Patrol"},
    {"name": "MP Nagar Main Spine (Zone 1 to Board Office)", "coords": [[23.2380, 77.4310], [23.2330, 77.4340], [23.2280, 77.4370]], "status": "Illuminated & Police Kiosks"},
    {"name": "Arera Link Road No. 1 Corridor", "coords": [[23.2250, 77.4200], [23.2130, 77.4280], [23.2040, 77.4340]], "status": "Smart Lighting & SOS Nodes"}
]


def generate_crime_dataset(n_samples: int = 480, seed: int = 42) -> pd.DataFrame:
    """
    Generates a realistic, statistically calibrated crime dataset for Bhopal.
    Includes incident ID, geo coordinates, neighborhood, crime category,
    specific subtype, time of day, datetime, severity score, and resolution status.
    """
    np.random.seed(seed)
    
    neighborhood_names = list(NEIGHBORHOOD_CONFIG.keys())
    weights = [NEIGHBORHOOD_CONFIG[n]["base_weight"] for n in neighborhood_names]
    weights = np.array(weights) / sum(weights)
    
    # Pick neighborhoods per sample
    chosen_neighborhoods = np.random.choice(neighborhood_names, size=n_samples, p=weights)
    
    records = []
    base_date = datetime.now() - timedelta(days=90)
    
    for i, nh_name in enumerate(chosen_neighborhoods):
        cfg = NEIGHBORHOOD_CONFIG[nh_name]
        
        # Spatial generation: Gaussian offset around neighborhood center
        lat = cfg["lat"] + np.random.normal(0, cfg["spread"] * 0.75)
        lon = cfg["lon"] + np.random.normal(0, cfg["spread"] * 0.75)
        
        # Boundary clamp to Bhopal metro area (23.14 to 23.32 N, 77.35 to 77.49 E)
        lat = float(np.clip(lat, 23.1450, 23.3250))
        lon = float(np.clip(lon, 77.3550, 77.4950))
        
        # Pick category based on neighborhood-specific crime weights
        cat_choices = list(cfg["crime_prop"].keys())
        cat_probs = list(cfg["crime_prop"].values())
        cat_probs = np.array(cat_probs) / sum(cat_probs)
        category = np.random.choice(cat_choices, p=cat_probs)
        
        # Subtype and severity
        detail_cfg = CRIME_DETAILS[category]
        subtype = np.random.choice(detail_cfg["subtypes"])
        severity = int(np.random.choice(detail_cfg["base_severity"], p=detail_cfg["severity_weights"]))
        
        # Time of day simulation
        is_night = np.random.random() < cfg["night_bias"]
        if is_night:
            time_of_day = "Nighttime/Post-10 PM"
            # Random hour between 22:00 and 04:59
            hour = np.random.choice([22, 23, 0, 1, 2, 3, 4])
            # Higher probability of severity increment at late night
            if severity < 5 and np.random.random() < 0.25:
                severity += 1
        else:
            time_of_day = "Daytime"
            hour = np.random.randint(6, 22)
            
        minute = np.random.randint(0, 60)
        day_offset = np.random.randint(0, 90)
        timestamp = base_date + timedelta(days=day_offset, hours=int(hour), minutes=int(minute))
        
        # Investigation / FIR status
        status_opts = ["FIR Registered", "Under Investigation", "Action Dispatched", "Resolved / Arrest Made"]
        status = np.random.choice(status_opts, p=[0.40, 0.35, 0.15, 0.10])
        
        incident_id = f"BHP-{timestamp.strftime('%Y')}-{1000 + i}"
        
        records.append({
            "incident_id": incident_id,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "neighborhood": nh_name,
            "zone_type": cfg["zone_type"],
            "crime_category": category,
            "crime_subtype": subtype,
            "time_of_day": time_of_day,
            "hour": hour,
            "date": timestamp.date(),
            "timestamp": timestamp,
            "severity_score": severity,
            "status": status
        })
        
    df = pd.DataFrame(records)
    # Sort by timestamp descending
    df = df.sort_values(by="timestamp", ascending=False).reset_index(drop=True)
    return df


def to_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Converts standard pandas DataFrame with latitude and longitude into
    a GeoPandas GeoDataFrame with WGS84 CRS (EPSG:4326).
    """
    geometry = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    return gdf


if __name__ == "__main__":
    df = generate_crime_dataset(100)
    print(f"Generated {len(df)} records.")
    print(df.head(3)[["incident_id", "neighborhood", "crime_category", "time_of_day", "severity_score"]])
