"""
================================================================================
Bhopal Safety Intelligence - Data Quality & Schema Validator
================================================================================
Validates incoming incident records against municipal bounding boxes, 
data types, categorical constraints, and duplicate identifiers.
Logs all validation errors instead of silently ignoring them.
================================================================================
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Configure standard logger
logger = logging.getLogger("bhopal_safety.validator")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [Validator] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Bhopal Municipal Geographic Bounding Box (including metropolitan urban periphery)
BHOPAL_BBOX = {
    "lat_min": 23.0000,
    "lat_max": 23.4500,
    "lon_min": 77.2000,
    "lon_max": 77.6500,
}

RECOGNIZED_CATEGORIES = {
    "Property Crime & Theft",
    "Violent Assault",
    "Women Safety Concerns",
    "Public Vandalism",
}

SEVERITY_MIN = 1
SEVERITY_MAX = 5


@dataclass
class ValidationIssue:
    row_id: Any
    field: str
    issue_type: str
    severity: str  # 'WARNING' or 'ERROR'
    message: str


@dataclass
class ValidationReport:
    total_records: int = 0
    valid_records: int = 0
    dropped_records: int = 0
    quality_score: float = 100.0
    issues: List[ValidationIssue] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "dropped_records": self.dropped_records,
            "quality_score": round(self.quality_score, 1),
            "issue_count": len(self.issues),
            "issues_summary": [
                {
                    "row_id": str(i.row_id),
                    "field": i.field,
                    "issue_type": i.issue_type,
                    "severity": i.severity,
                    "message": i.message,
                }
                for i in self.issues[:20]  # sample top 20
            ],
            "timestamp": self.timestamp,
        }


def validate_crime_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, ValidationReport]:
    """
    Validates a DataFrame of crime incidents.
    Returns:
        clean_df: DataFrame containing only sanitized and valid records.
        report: ValidationReport detailing metrics, dropped rows, and issues.
    """
    report = ValidationReport(total_records=len(df))
    if df.empty:
        logger.warning("Empty DataFrame provided for validation.")
        report.quality_score = 0.0
        return df.copy(), report

    clean_mask = np.ones(len(df), dtype=bool)
    issues: List[ValidationIssue] = []

    # 1. Check Missing Coordinates
    missing_coords = df["latitude"].isna() | df["longitude"].isna()
    for idx in df[missing_coords].index:
        row_id = df.loc[idx, "incident_id"] if "incident_id" in df.columns else idx
        issues.append(ValidationIssue(
            row_id=row_id,
            field="coordinates",
            issue_type="MISSING_COORDINATES",
            severity="ERROR",
            message="Latitude or Longitude is null or unparseable."
        ))
        clean_mask[idx] = False
    
    # 2. Check Bounding Box (Bhopal region)
    valid_coords = ~missing_coords
    lat_series = pd.to_numeric(df.loc[valid_coords, "latitude"], errors="coerce")
    lon_series = pd.to_numeric(df.loc[valid_coords, "longitude"], errors="coerce")

    out_of_bounds = (
        (lat_series < BHOPAL_BBOX["lat_min"]) |
        (lat_series > BHOPAL_BBOX["lat_max"]) |
        (lon_series < BHOPAL_BBOX["lon_min"]) |
        (lon_series > BHOPAL_BBOX["lon_max"])
    )
    for idx in lat_series[out_of_bounds].index:
        row_id = df.loc[idx, "incident_id"] if "incident_id" in df.columns else idx
        issues.append(ValidationIssue(
            row_id=row_id,
            field="coordinates",
            issue_type="OUT_OF_BOUNDS_COORDINATES",
            severity="ERROR",
            message=f"Coordinates ({df.loc[idx, 'latitude']}, {df.loc[idx, 'longitude']}) outside Bhopal municipal bounding box."
        ))
        clean_mask[idx] = False

    # 3. Check Duplicate Incident IDs
    if "incident_id" in df.columns:
        dup_mask = df.duplicated(subset=["incident_id"], keep="first")
        for idx in df[dup_mask].index:
            row_id = df.loc[idx, "incident_id"]
            issues.append(ValidationIssue(
                row_id=row_id,
                field="incident_id",
                issue_type="DUPLICATE_ID",
                severity="ERROR",
                message=f"Duplicate incident ID '{row_id}' found. Keeping first occurrence."
            ))
            clean_mask[idx] = False

    # 4. Check Severity Bounds
    if "severity" in df.columns:
        sev_numeric = pd.to_numeric(df["severity"], errors="coerce")
        invalid_sev = (sev_numeric < SEVERITY_MIN) | (sev_numeric > SEVERITY_MAX) | sev_numeric.isna()
        for idx in df[invalid_sev].index:
            row_id = df.loc[idx, "incident_id"] if "incident_id" in df.columns else idx
            issues.append(ValidationIssue(
                row_id=row_id,
                field="severity",
                issue_type="INVALID_SEVERITY",
                severity="WARNING",
                message=f"Severity value '{df.loc[idx, 'severity']}' outside [{SEVERITY_MIN}, {SEVERITY_MAX}]. Coercing to 3 (Medium)."
            ))
            # Coerce rather than drop for warnings
            df.loc[idx, "severity"] = 3

    # 5. Check Category Validity
    if "category" in df.columns:
        for idx in df.index:
            cat = str(df.loc[idx, "category"]).strip()
            if cat not in RECOGNIZED_CATEGORIES:
                row_id = df.loc[idx, "incident_id"] if "incident_id" in df.columns else idx
                issues.append(ValidationIssue(
                    row_id=row_id,
                    field="category",
                    issue_type="UNRECOGNIZED_CATEGORY",
                    severity="WARNING",
                    message=f"Category '{cat}' is not in standard ontology. Remapping to 'Property Crime & Theft'."
                ))
                df.loc[idx, "category"] = "Property Crime & Theft"

    # Compile report
    report.issues = issues
    report.dropped_records = int(np.sum(~clean_mask))
    report.valid_records = int(np.sum(clean_mask))
    if report.total_records > 0:
        penalty = (report.dropped_records * 2.0 + len(issues) * 0.5) / report.total_records * 100
        report.quality_score = max(0.0, min(100.0, 100.0 - penalty))

    logger.info(
        f"Validation Complete: Total={report.total_records}, Valid={report.valid_records}, "
        f"Dropped={report.dropped_records}, QualityScore={report.quality_score:.1f}%"
    )

    clean_df = df[clean_mask].copy().reset_index(drop=True)
    return clean_df, report
