import numpy as np
import pandas as pd

from ml.preprocessing.pipeline import make_preprocessor
from ml.features.dynamic import add_longitudinal_features


def row():
    return pd.DataFrame([{
        "interaction_number": 1, "days_since_registration": 0, "age": 30,
        "severity_1_to_5": 3, "threat_received": 0,
        "investigation_or_court_delay_days": 20, "court_appearances_to_date": 0,
        "economic_stress_1_to_5": 2, "social_support_1_to_5": 4,
        "sentiment_score": 0.1, "fear_score": 0.2, "sadness_score": 0.2,
        "anger_score": 0.1, "voice_stress_score": 0.2, "engagement_score": 0.8,
        "current_distress_score": 35,
        "state": "known_state", "gender": "unknown_gender", "social_category":"X",
        "offence_type":"unknown_offence", "case_stage":"new_stage",
        "communication_channel":"unknown_channel", "relief_status":"pending",
        "counselling_status":"not_provided",
    }])


def test_unknown_categories_are_ignored():
    train=row().copy()
    train["state"]="train_state"; train["gender"]="female"; train["social_category"]="SC"
    train["offence_type"]="rape"; train["case_stage"]="trial"
    train["communication_channel"]="chatbot"
    train=add_longitudinal_features(train.assign(victim_id='T1'))
    test=add_longitudinal_features(row().assign(victim_id='U1'))
    pre=make_preprocessor("dynamic")
    x=pre.fit_transform(train)
    y=pre.transform(test)
    assert x.shape[1]==y.shape[1]


def test_missing_numeric_value_is_imputed():
    train=row().copy()
    train["state"]="train_state"; train["gender"]="female"; train["social_category"]="SC"
    train["offence_type"]="rape"; train["case_stage"]="trial"; train["communication_channel"]="chatbot"
    train["current_distress_score"]=np.nan
    train=add_longitudinal_features(train.assign(victim_id='T1'))
    pre=make_preprocessor("dynamic")
    x=pre.fit_transform(train)
    assert np.isfinite(x).all()
