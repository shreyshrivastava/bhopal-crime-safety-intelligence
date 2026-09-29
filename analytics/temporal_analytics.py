"""
================================================================================
Bhopal Safety Intelligence - Temporal Analytics Engine
================================================================================
Evaluates time-series velocities, diurnal distributions, weekend/weekday surges,
and temporal severity shifts across the incident records.
================================================================================
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd
import numpy as np


def analyze_temporal_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes temporal velocities, diurnal distribution, and day-of-week patterns.
    """
    if df.empty:
        return {
            "total_incidents": 0,
            "velocity_7d": 0.0,
            "velocity_30d": 0.0,
            "trend_direction": "Stable",
            "night_ratio_pct": 0.0,
            "day_avg_severity": 0.0,
            "night_avg_severity": 0.0,
            "diurnal_breakdown": {},
            "dow_breakdown": {},
            "hourly_distribution": [0] * 24,
        }

    temp_df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(temp_df["timestamp"]):
        temp_df["timestamp"] = pd.to_datetime(temp_df["timestamp"], errors="coerce").fillna(pd.to_datetime(datetime.now()))

    now = temp_df["timestamp"].max()
    t7 = now - timedelta(days=7)
    t14 = now - timedelta(days=14)
    t30 = now - timedelta(days=30)
    t60 = now - timedelta(days=60)

    # 1. Recent Velocity Calculations
    count_last_7d = len(temp_df[temp_df["timestamp"] >= t7])
    count_prev_7d = len(temp_df[(temp_df["timestamp"] >= t14) & (temp_df["timestamp"] < t7)])
    
    velocity_7d_pct = 0.0
    if count_prev_7d > 0:
        velocity_7d_pct = round(((count_last_7d - count_prev_7d) / count_prev_7d) * 100, 1)

    count_last_30d = len(temp_df[temp_df["timestamp"] >= t30])
    count_prev_30d = len(temp_df[(temp_df["timestamp"] >= t60) & (temp_df["timestamp"] < t30)])
    
    velocity_30d_pct = 0.0
    if count_prev_30d > 0:
        velocity_30d_pct = round(((count_last_30d - count_prev_30d) / count_prev_30d) * 100, 1)

    if velocity_7d_pct > 5.0:
        trend_direction = "Surging Upward"
    elif velocity_7d_pct < -5.0:
        trend_direction = "Declining"
    else:
        trend_direction = "Stable"

    # 2. Night vs Day Severity Shift
    sev_col = "severity" if "severity" in temp_df.columns else ("severity_score" if "severity_score" in temp_df.columns else "severity")
    night_mask = temp_df["time_of_day"].astype(str).str.lower().str.contains("night")
    night_count = int(np.sum(night_mask))
    day_count = len(temp_df) - night_count
    night_ratio = round((night_count / len(temp_df)) * 100, 1) if len(temp_df) > 0 else 0.0

    day_avg_sev = round(float(pd.to_numeric(temp_df.loc[~night_mask, sev_col], errors="coerce").mean()), 2) if day_count > 0 else 0.0
    night_avg_sev = round(float(pd.to_numeric(temp_df.loc[night_mask, sev_col], errors="coerce").mean()), 2) if night_count > 0 else 0.0

    # 3. Hourly & Diurnal Distribution
    hours = temp_df["timestamp"].dt.hour
    hourly_counts = [int(np.sum(hours == h)) for h in range(24)]

    # Diurnal slots:
    # Early Morning: 04:00 - 08:00
    # Day Peak: 08:00 - 16:00
    # Evening Rush: 16:00 - 21:00
    # Night Watch: 21:00 - 04:00
    early_morning = int(np.sum((hours >= 4) & (hours < 8)))
    day_peak = int(np.sum((hours >= 8) & (hours < 16)))
    evening_rush = int(np.sum((hours >= 16) & (hours < 21)))
    night_watch = len(temp_df) - (early_morning + day_peak + evening_rush)

    diurnal_breakdown = {
        "Early Morning (04:00-08:00)": {"count": early_morning, "pct": round(early_morning / len(temp_df) * 100, 1)},
        "Day Commercial (08:00-16:00)": {"count": day_peak, "pct": round(day_peak / len(temp_df) * 100, 1)},
        "Evening Transit (16:00-21:00)": {"count": evening_rush, "pct": round(evening_rush / len(temp_df) * 100, 1)},
        "Night Watch (21:00-04:00)": {"count": night_watch, "pct": round(night_watch / len(temp_df) * 100, 1)},
    }

    # 4. Day of Week Breakdown
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dows = temp_df["timestamp"].dt.dayofweek
    dow_counts = {day_names[i]: int(np.sum(dows == i)) for i in range(7)}

    return {
        "total_incidents": len(temp_df),
        "last_7d_count": count_last_7d,
        "velocity_7d_pct": velocity_7d_pct,
        "last_30d_count": count_last_30d,
        "velocity_30d_pct": velocity_30d_pct,
        "trend_direction": trend_direction,
        "night_ratio_pct": night_ratio,
        "day_avg_severity": day_avg_sev,
        "night_avg_severity": night_avg_sev,
        "severity_differential": round(night_avg_sev - day_avg_sev, 2),
        "diurnal_breakdown": diurnal_breakdown,
        "dow_breakdown": dow_counts,
        "hourly_distribution": hourly_counts,
    }
