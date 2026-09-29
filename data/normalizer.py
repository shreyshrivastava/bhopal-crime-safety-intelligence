"""
================================================================================
Bhopal Safety Intelligence - Schema Normalizer
================================================================================
Normalizes raw heterogeneous crime incident records from various public / 
benchmark formats into the standardized internal schema.
================================================================================
"""

from datetime import datetime
from typing import Dict, Any
import pandas as pd
import numpy as np

# Standard Column Aliases Mapping
COLUMN_ALIASES = {
    "latitude": ["lat", "Latitude", "LAT", "y", "coord_y", "geo_lat"],
    "longitude": ["lon", "lng", "Longitude", "LON", "LNG", "x", "coord_x", "geo_lon"],
    "incident_id": ["id", "fir_no", "FIR_NO", "case_id", "incident_no", "report_id"],
    "category": ["crime_category", "type", "offense_group", "major_category"],
    "offense_type": ["offense", "sub_category", "ipc_section", "incident_type", "description"],
    "severity": ["severity_score", "risk_level", "priority", "gravity"],
    "sector": ["area", "neighborhood", "locality", "zone_name", "suburb"],
    "ward_no": ["ward", "ward_number", "municipal_ward", "ward_id"],
    "date": ["incident_date", "occurred_on", "event_date"],
    "timestamp": ["datetime", "incident_time", "created_at", "reported_time"],
}


def normalize_crime_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes column names, types, and values into the uniform internal format.
    """
    if df.empty:
        return df.copy()

    norm_df = df.copy()

    # 1. Alias Resolution
    for standard_col, aliases in COLUMN_ALIASES.items():
        if standard_col not in norm_df.columns:
            for alias in aliases:
                if alias in norm_df.columns:
                    norm_df.rename(columns={alias: standard_col}, inplace=True)
                    break

    # 2. Ensure Required Identifiers
    if "incident_id" not in norm_df.columns:
        norm_df["incident_id"] = [f"INC-{1000 + i}" for i in range(len(norm_df))]
    else:
        norm_df["incident_id"] = norm_df["incident_id"].astype(str)

    # 3. Numeric Conversions
    norm_df["latitude"] = pd.to_numeric(norm_df["latitude"], errors="coerce")
    norm_df["longitude"] = pd.to_numeric(norm_df["longitude"], errors="coerce")

    if "severity" in norm_df.columns:
        norm_df["severity"] = pd.to_numeric(norm_df["severity"], errors="coerce").fillna(3).astype(int)
    else:
        norm_df["severity"] = 3

    if "ward_no" in norm_df.columns:
        norm_df["ward_no"] = pd.to_numeric(norm_df["ward_no"], errors="coerce").fillna(1).astype(int)
    else:
        norm_df["ward_no"] = 1

    # 4. Standardize Dates & Timestamps
    if "timestamp" in norm_df.columns:
        norm_df["timestamp"] = pd.to_datetime(norm_df["timestamp"], errors="coerce")
    elif "date" in norm_df.columns:
        norm_df["timestamp"] = pd.to_datetime(norm_df["date"], errors="coerce")
    else:
        norm_df["timestamp"] = pd.to_datetime(datetime.now())

    # Fill invalid timestamps with current time
    norm_df["timestamp"] = norm_df["timestamp"].fillna(pd.to_datetime(datetime.now()))
    norm_df["date"] = norm_df["timestamp"].dt.strftime("%Y-%m-%d")

    # 5. Determine Day / Night Temporal Class
    if "time_of_day" not in norm_df.columns:
        hours = norm_df["timestamp"].dt.hour
        # Indian civic policing standard: 20:00 - 05:00 is Night
        norm_df["time_of_day"] = np.where((hours >= 20) | (hours < 6), "Night", "Day")
    else:
        norm_df["time_of_day"] = np.where(
            norm_df["time_of_day"].astype(str).str.lower().str.contains("night"),
            "Night",
            "Day"
        )

    # 6. Sector & Locality Defaults
    if "sector" not in norm_df.columns:
        if "neighborhood" in norm_df.columns:
            norm_df["sector"] = norm_df["neighborhood"]
        else:
            norm_df["sector"] = "Bhopal Central"
    norm_df["sector"] = norm_df["sector"].astype(str).str.strip()

    # 7. Category & Offense Normalization
    category_map = {
        "Assault & Physical Offenses": "Violent Assault",
        "Public Harassment / Women's Safety": "Women Safety Concerns",
        "Vandalism / Petty Mischief": "Public Vandalism",
        "Property Crime & Theft": "Property Crime & Theft",
    }
    if "category" in norm_df.columns:
        norm_df["category"] = norm_df["category"].replace(category_map)
    elif "crime_category" in norm_df.columns:
        norm_df["category"] = norm_df["crime_category"].replace(category_map)
    else:
        norm_df["category"] = "Property Crime & Theft"
    norm_df["category"] = norm_df["category"].astype(str).str.strip()

    if "offense_type" not in norm_df.columns:
        norm_df["offense_type"] = norm_df["category"]
    norm_df["offense_type"] = norm_df["offense_type"].astype(str).str.strip()

    if "status" not in norm_df.columns:
        norm_df["status"] = "Under Investigation"
    if "resolved" not in norm_df.columns:
        norm_df["resolved"] = False

    return norm_df
