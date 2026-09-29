"""
================================================================================
Bhopal Safety Intelligence - Spatial-Temporal Anomaly Detection
================================================================================
Uses unsupervised Isolation Forest to identify statistical spatial-temporal outliers 
(e.g., severe crimes in typically quiet residential zones, uncharacteristic 
midnight surges, or rare offense modalities).
================================================================================
"""

import logging
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger("bhopal_safety.anomaly")


def detect_crime_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> List[Dict[str, Any]]:
    """
    Fits an Isolation Forest to detect atypical crime events.
    Returns:
        List of anomaly records with geographic coordinates, anomaly scores, and human-interpretable reasons.
    """
    if df.empty or len(df) < 20:
        return []

    logger.info(f"Running Isolation Forest anomaly detection (contamination={contamination})...")

    # Feature extraction for unsupervised outlier modeling
    sev_col = "severity" if "severity" in df.columns else ("severity_score" if "severity_score" in df.columns else "severity")
    sector_col = "sector" if "sector" in df.columns else ("neighborhood" if "neighborhood" in df.columns else "sector")
    cat_col = "category" if "category" in df.columns else ("crime_category" if "crime_category" in df.columns else "category")
    off_col = "offense_type" if "offense_type" in df.columns else ("crime_subtype" if "crime_subtype" in df.columns else "offense_type")

    lats = pd.to_numeric(df["latitude"], errors="coerce").fillna(23.25).values
    lons = pd.to_numeric(df["longitude"], errors="coerce").fillna(77.41).values
    sevs = pd.to_numeric(df[sev_col], errors="coerce").fillna(3.0).values
    is_night = (df["time_of_day"].astype(str).str.lower().str.contains("night")).astype(float).values

    # Parse hour if available
    if "hour" in df.columns:
        hours = pd.to_numeric(df["hour"], errors="coerce").fillna(12.0).values
    elif "timestamp" in df.columns and pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        hours = df["timestamp"].dt.hour.values
    else:
        hours = np.where(is_night == 1.0, 23.0, 14.0)

    # Normalize features for uniform tree splitting
    X = np.column_stack([
        (lats - np.mean(lats)) / (np.std(lats) + 1e-6),
        (lons - np.mean(lons)) / (np.std(lons) + 1e-6),
        (sevs - np.mean(sevs)) / (np.std(sevs) + 1e-6),
        is_night,
        hours / 24.0,
    ])

    iso = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    preds = iso.fit_predict(X)
    scores = iso.decision_function(X) # lower score = more anomalous

    anomalies = []
    outlier_indices = np.where(preds == -1)[0]

    for idx in outlier_indices:
        row = df.iloc[idx]
        score = float(scores[idx])
        sev = int(row.get(sev_col, 3))
        tod = str(row.get("time_of_day", ""))
        sector = str(row.get(sector_col, "Bhopal Sector"))
        cat = str(row.get(cat_col, "General Offense"))
        offense = str(row.get(off_col, "Incident"))

        # Determine human-interpretable rationale
        reasons = []
        if sev >= 4:
            reasons.append(f"Critical Severity ({sev}/5) in {sector}")
        if "night" in tod.lower() and "assault" in cat.lower():
            reasons.append("Late-Night Violent Assault Pattern")
        elif "women" in cat.lower() or "harassment" in cat.lower():
            reasons.append("High-Priority Women Safety Outlier")
        elif sev >= 4 and "theft" in cat.lower():
            reasons.append("Aggravated Major Property Crime")
        else:
            reasons.append("Spatial Coordinate / Temporal Isolation")

        reason_str = " & ".join(reasons)

        anomalies.append({
            "incident_id": str(row.get("incident_id", f"INC-{idx}")),
            "latitude": round(float(row.get("latitude", 23.25)), 5),
            "longitude": round(float(row.get("longitude", 77.41)), 5),
            "category": cat,
            "offense_type": offense,
            "severity": sev,
            "sector": sector,
            "time_of_day": tod,
            "date": str(row.get("date", "Recent")),
            "anomaly_score": round(abs(score) * 100.0, 1),
            "reason": reason_str,
        })

    # Sort by anomaly severity
    anomalies.sort(key=lambda a: a["anomaly_score"], reverse=True)
    logger.info(f"Detected {len(anomalies)} crime anomalies.")
    return anomalies
