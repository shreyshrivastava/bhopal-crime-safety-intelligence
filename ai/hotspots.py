"""
================================================================================
Bhopal Safety Intelligence - DBSCAN Hotspot & Emerging Cluster Engine
================================================================================
Executes spatial clustering using DBSCAN with Great-Circle Haversine distance
to isolate dense incident epicenters and detect emerging crime hotspots.
================================================================================
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

logger = logging.getLogger("bhopal_safety.hotspots")

EARTH_RADIUS_KM = 6371.0


def detect_spatial_hotspots(
    df: pd.DataFrame,
    eps_meters: float = 750.0,
    min_samples: int = 10
) -> List[Dict[str, Any]]:
    """
    Identifies high-density spatial clusters and evaluates emergence velocity.
    """
    if df.empty or len(df) < min_samples:
        return []

    logger.info(f"Running DBSCAN hotspot clustering (eps={eps_meters}m, min_samples={min_samples})...")

    # Extract coordinates and convert to radians for spherical Haversine metric
    coords = df[["latitude", "longitude"]].dropna().values
    rad_coords = np.radians(coords)
    eps_radians = (eps_meters / 1000.0) / EARTH_RADIUS_KM

    db = DBSCAN(eps=eps_radians, min_samples=min_samples, metric="haversine", algorithm="ball_tree")
    labels = db.fit_predict(rad_coords)

    unique_labels = set(labels)
    if -1 in unique_labels:
        unique_labels.remove(-1) # Remove noise

    hotspots = []
    now = pd.to_datetime(df["timestamp"].max()) if "timestamp" in df.columns else pd.to_datetime(datetime.now())
    t30 = now - timedelta(days=30)

    for cluster_id in sorted(unique_labels):
        cluster_mask = (labels == cluster_id)
        cluster_df = df.iloc[cluster_mask]
        cluster_size = len(cluster_df)

        # Calculate centroid
        c_lat = float(cluster_df["latitude"].mean())
        c_lon = float(cluster_df["longitude"].mean())

        # Calculate spread radius (90th percentile distance from centroid in meters)
        dists = np.sqrt(
            (cluster_df["latitude"].values - c_lat) ** 2 +
            (cluster_df["longitude"].values - c_lon) ** 2
        ) * 111000.0 # meters approx
        radius_m = float(np.percentile(dists, 85)) if len(dists) > 0 else eps_meters

        # Dominant Category & Sector
        sev_col = "severity" if "severity" in cluster_df.columns else ("severity_score" if "severity_score" in cluster_df.columns else "severity")
        cat_col = "category" if "category" in cluster_df.columns else ("crime_category" if "crime_category" in cluster_df.columns else "category")
        sec_col = "sector" if "sector" in cluster_df.columns else ("neighborhood" if "neighborhood" in cluster_df.columns else "sector")

        dominant_cat = cluster_df[cat_col].mode().iloc[0] if cat_col in cluster_df.columns and not cluster_df[cat_col].empty else "General"
        primary_sector = cluster_df[sec_col].mode().iloc[0] if sec_col in cluster_df.columns and not cluster_df[sec_col].empty else "Bhopal"
        avg_sev = round(float(pd.to_numeric(cluster_df[sev_col], errors="coerce").fillna(3.0).mean()), 2)

        # Check for Emerging Hotspot (> 45% of cluster events occurred in past 30 days)
        if "timestamp" in cluster_df.columns:
            recent_count = len(cluster_df[pd.to_datetime(cluster_df["timestamp"], errors="coerce") >= t30])
            recent_pct = round((recent_count / cluster_size) * 100.0, 1)
        else:
            recent_pct = 50.0

        is_emerging = recent_pct >= 45.0 and cluster_size >= 12
        cluster_status = "Emerging Hotspot" if is_emerging else "Established Hotspot"

        hotspots.append({
            "cluster_id": int(cluster_id) + 1,
            "name": f"Hotspot Cluster #{cluster_id + 1} ({primary_sector})",
            "sector": primary_sector,
            "centroid_lat": round(c_lat, 5),
            "centroid_lon": round(c_lon, 5),
            "radius_meters": round(max(300.0, radius_m), 0),
            "incident_count": int(cluster_size),
            "dominant_category": dominant_cat,
            "average_severity": avg_sev,
            "recent_30d_pct": recent_pct,
            "is_emerging": is_emerging,
            "status": cluster_status,
            "badge_class": "bg-rose-500/25 text-rose-300 border-rose-500/40" if is_emerging else "bg-amber-500/25 text-amber-300 border-amber-500/40"
        })

    # Sort clusters by incident volume
    hotspots.sort(key=lambda h: (h["is_emerging"], h["incident_count"]), reverse=True)
    logger.info(f"Identified {len(hotspots)} distinct density clusters.")
    return hotspots
