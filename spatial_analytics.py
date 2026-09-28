"""
Bhopal Crime & Safety Intelligence Dashboard
Geospatial Analytics & Proximity Engine
Calculates spatial proximity, sector risk indices, and safety metrics.
Uses vectorized geodesic Haversine distance for 100% thread/fork safety on macOS Apple Silicon.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from data_generator import POLICE_STATIONS, NEIGHBORHOOD_CONFIG


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """
    Computes high-precision great-circle distance between coordinates on Earth in kilometers.
    Vectorized with NumPy for maximum performance and fork-safety.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    return R * c


def get_police_stations_gdf() -> gpd.GeoDataFrame:
    """
    Creates a GeoDataFrame of Bhopal Police Stations in WGS84 CRS (EPSG:4326).
    """
    df_ps = pd.DataFrame(POLICE_STATIONS)
    geometry = [Point(xy) for xy in zip(df_ps["lon"], df_ps["lat"])]
    gdf_ps = gpd.GeoDataFrame(df_ps, geometry=geometry, crs="EPSG:4326")
    return gdf_ps


def calculate_station_proximity(crime_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calculates the geodesic distance in kilometers from each crime incident to the closest
    Bhopal Police Station using vectorized Haversine formula.
    
    Fork-safe & thread-safe across all platforms (macOS Apple Silicon & Linux Cloud).
    """
    if crime_gdf.empty:
        crime_gdf = crime_gdf.copy()
        crime_gdf["nearest_station"] = None
        crime_gdf["distance_to_station_km"] = 0.0
        return crime_gdf

    ps_df = pd.DataFrame(POLICE_STATIONS)
    ps_lats = ps_df["lat"].values
    ps_lons = ps_df["lon"].values
    ps_names = ps_df["name"].values

    crime_lats = crime_gdf["latitude"].values[:, np.newaxis]
    crime_lons = crime_gdf["longitude"].values[:, np.newaxis]

    # Matrix of distances between N incidents and M stations (shape: N x M)
    dists = haversine_distance_km(crime_lats, crime_lons, ps_lats, ps_lons)
    min_indices = np.argmin(dists, axis=1)

    crime_gdf = crime_gdf.copy()
    crime_gdf["nearest_station"] = ps_names[min_indices]
    crime_gdf["distance_to_station_km"] = np.round(
        dists[np.arange(len(crime_gdf)), min_indices], 2
    )
    return crime_gdf


def compute_sector_risk_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes a composite Safety & Risk Index for each Bhopal neighborhood.
    Metrics evaluated:
    - Incident volume
    - Average severity score (1-5)
    - High-severity incident count (severity >= 4)
    - Nighttime incident ratio
    - Composite Risk Index (0-100 scale, where higher = higher risk / lower safety)
    """
    if df.empty:
        return pd.DataFrame()

    summary = []
    for neighborhood, group in df.groupby("neighborhood"):
        count = len(group)
        avg_sev = group["severity_score"].mean()
        high_sev_count = (group["severity_score"] >= 4).sum()
        night_ratio = (group["time_of_day"] == "Nighttime/Post-10 PM").mean()
        
        # Primary crime type
        top_crime = group["crime_category"].mode()[0] if not group.empty else "N/A"
        
        # Composite score normalized
        # Weights: 40% incident volume (scaled), 35% severity, 25% night ratio
        vol_score = min(count / 30.0, 1.0) * 40.0
        sev_score = ((avg_sev - 1.0) / 4.0) * 35.0
        night_score = night_ratio * 25.0
        composite_risk = round(vol_score + sev_score + night_score, 1)
        
        # Safety rating tier
        if composite_risk < 35:
            risk_tier = "Low Risk / Safe"
            badge_color = "#10B981"
        elif composite_risk < 60:
            risk_tier = "Moderate Risk"
            badge_color = "#F59E0B"
        elif composite_risk < 80:
            risk_tier = "Elevated Risk"
            badge_color = "#EF4444"
        else:
            risk_tier = "Critical Hotspot"
            badge_color = "#991B1B"
            
        summary.append({
            "Neighborhood": neighborhood,
            "Incidents": count,
            "Avg Severity": round(avg_sev, 2),
            "High Severity Count": int(high_sev_count),
            "Nighttime Ratio (%)": round(night_ratio * 100, 1),
            "Dominant Crime": top_crime,
            "Risk Score": composite_risk,
            "Risk Level": risk_tier,
            "Badge Color": badge_color
        })

    result_df = pd.DataFrame(summary).sort_values(by="Risk Score", ascending=False).reset_index(drop=True)
    return result_df


if __name__ == "__main__":
    from data_generator import generate_crime_dataset, to_geodataframe
    df = generate_crime_dataset(150)
    gdf = to_geodataframe(df)
    gdf_with_prox = calculate_station_proximity(gdf)
    print("Calculated Proximities:")
    print(gdf_with_prox[["incident_id", "neighborhood", "nearest_station", "distance_to_station_km"]].head(3))
    risk_df = compute_sector_risk_index(df)
    print("\nSector Risk Summary:")
    print(risk_df.head(4))
