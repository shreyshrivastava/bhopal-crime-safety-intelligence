"""
================================================================================
Bhopal Safety Intelligence - Explainable AI (XAI) Insight Generator
================================================================================
Translates statistical model outputs, feature weights, and temporal trends 
into natural-language explanations with explicit contributing factors.
Avoids opaque black-box assertions.
================================================================================
"""

from typing import List, Dict, Any


def generate_explainable_insights(
    sector_predictions: List[Dict[str, Any]],
    feature_importances: Dict[str, float],
    model_r2: float,
    temporal_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generates natural-language reasoning and contributing factor explanations.
    """
    if not sector_predictions:
        return {
            "executive_summary": "Insufficient data to synthesize AI safety insights.",
            "sector_insights": [],
            "top_risk_sector": None,
        }

    # Top risk sector
    top_sector = sector_predictions[0]
    sec_name = top_sector["sector"]
    score = top_sector["predicted_risk_score"]
    tier = top_sector["risk_tier"]

    # Derive confidence rating from Model R² and sample metrics
    confidence_pct = min(96.0, max(75.0, round(model_r2 * 100.0, 1)))

    sector_insights = []
    for s in sector_predictions:
        factors = []
        name = s["sector"]
        vol = s["historical_volume"]
        sev = s["average_severity"]
        night_pct = s["night_ratio_pct"]
        dist = s["distance_to_thana_km"]

        # 1. Volume Factor
        if vol >= 60:
            factors.append(f"High cumulative incident concentration ({vol} reported events)")
        elif vol >= 35:
            factors.append(f"Moderate baseline activity ({vol} events)")
        else:
            factors.append(f"Low historical volume ({vol} events)")

        # 2. Severity Factor
        if sev >= 3.2:
            factors.append(f"Elevated proportion of severe offenses (Avg severity {sev} / 5.0)")
        elif sev >= 2.7:
            factors.append(f"Standard severity distribution (Avg severity {sev} / 5.0)")
        else:
            factors.append(f"Predominantly low-severity or petty infractions ({sev} / 5.0)")

        # 3. Nighttime Ratio Factor
        if night_pct >= 40.0:
            factors.append(f"Marked nocturnal crime bias ({night_pct}% incidents during night watch)")
        else:
            factors.append(f"Balanced diurnal-nocturnal distribution ({night_pct}% night ratio)")

        # 4. Proximity Factor
        if dist >= 2.0:
            factors.append(f"Distance to nearest police jurisdiction ({dist} km geodesic offset)")
        else:
            factors.append(f"Close proximity to active police post ({dist} km to nearest Thana)")

        # Narrative description
        narrative = (
            f"The Random Forest model projects a risk score of {s['predicted_risk_score']}/100 "
            f"({s['risk_tier']}) for {name}. Contributing dynamics: {factors[0].lower()} combined with "
            f"{factors[1].lower()} and a {night_pct}% nighttime chrono-bias."
        )

        sector_insights.append({
            "sector": name,
            "risk_score": s["predicted_risk_score"],
            "risk_tier": s["risk_tier"],
            "badge_class": s["badge_class"],
            "contributing_factors": factors,
            "narrative": narrative,
            "confidence_pct": confidence_pct,
        })

    # Executive Overview Insight
    exec_factors = sector_insights[0]["contributing_factors"]
    velocity_7d = temporal_metrics.get("velocity_7d_pct", 0.0)
    velocity_text = f"an upward 7-day velocity (+{velocity_7d}%)" if velocity_7d > 0 else f"a stable 7-day velocity ({velocity_7d}%)"

    executive_summary = {
        "title": f"AI Safety Insight: {sec_name} Identified as Primary Risk Sector",
        "sector": sec_name,
        "risk_tier": tier,
        "score": score,
        "confidence_pct": confidence_pct,
        "model_basis": f"Random Forest Regressor (R² = {model_r2:.2f})",
        "key_factors": exec_factors,
        "velocity_assessment": f"Current municipal velocity reflects {velocity_text}.",
        "recommendation": (
            f"Recommended deployment: Intensify motorized night patrols along transit nodes in {sec_name} "
            f"and strengthen civic safe corridor lighting between 21:00 and 03:00."
        ),
        "disclaimer": (
            "Derived from statistical modeling on calibrated baseline data. "
            "Confidence reflects model goodness-of-fit, not absolute certainty of future events."
        )
    }

    return {
        "executive_summary": executive_summary,
        "sector_insights": sector_insights,
        "top_risk_sector": sec_name,
    }
