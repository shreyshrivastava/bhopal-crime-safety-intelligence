"""
AI & Machine Learning Package for Bhopal Safety Intelligence.
Includes:
- Predictive Risk Modeling (Random Forest)
- Spatial-Temporal Anomaly Detection (Isolation Forest)
- Density Hotspot & Emerging Cluster Detection (DBSCAN)
- Interpretable Feature Attribution & Natural Language Explanations
"""
from .risk_model import train_and_evaluate_risk_model, ModelEvaluationResult
from .anomaly_detection import detect_crime_anomalies
from .hotspots import detect_spatial_hotspots
from .explanations import generate_explainable_insights

__all__ = [
    "train_and_evaluate_risk_model",
    "ModelEvaluationResult",
    "detect_crime_anomalies",
    "detect_spatial_hotspots",
    "generate_explainable_insights",
]
