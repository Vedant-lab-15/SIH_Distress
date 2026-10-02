from __future__ import annotations

from pathlib import Path

TARGET = "next_distress_score"

RAW_NUMERIC_FEATURES = [
    "interaction_number",
    "days_since_registration",
    "age",
    "severity_1_to_5",
    "threat_received",
    "investigation_or_court_delay_days",
    "court_appearances_to_date",
    "economic_stress_1_to_5",
    "social_support_1_to_5",
    "sentiment_score",
    "fear_score",
    "sadness_score",
    "anger_score",
    "voice_stress_score",
    "engagement_score",
    "current_distress_score",
]

CATEGORICAL_FEATURES = [
    "state",
    "gender",
    "social_category",
    "offence_type",
    "case_stage",
    "communication_channel",
    "relief_status",
    "counselling_status",
]

DYNAMIC_NUMERIC_FEATURES = [
    "distress_delta",
    "historical_distress_mean",
    "recent_distress_mean",
    "distress_momentum",
    "fear_change",
    "sadness_change",
    "voice_stress_change",
    "engagement_change",
    "has_previous_interaction",
]

STATIC_FEATURES = RAW_NUMERIC_FEATURES + CATEGORICAL_FEATURES
DYNAMIC_FEATURES = RAW_NUMERIC_FEATURES + DYNAMIC_NUMERIC_FEATURES + CATEGORICAL_FEATURES

LEAKAGE_COLUMNS = {
    TARGET,
    "risk_level",
    "intervention_triggered",
}

def validate_no_target_leakage(feature_names: list[str]) -> None:
    leaked = set(feature_names) & LEAKAGE_COLUMNS
    if leaked:
        raise AssertionError(f"Target leakage detected in model features: {sorted(leaked)}")
