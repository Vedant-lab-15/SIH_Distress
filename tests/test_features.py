import pandas as pd
import numpy as np

from ml.features.dynamic import add_longitudinal_features, trend_label


def sample():
    return pd.DataFrame({
        "victim_id": ["V1","V1","V1","V2"],
        "interaction_number": [1,2,3,1],
        "current_distress_score": [40.0,50.0,65.0,30.0],
        "fear_score": [0.2,0.4,0.8,0.3],
        "sadness_score": [0.3,0.5,0.6,0.2],
        "voice_stress_score": [0.2,0.3,0.6,0.2],
        "engagement_score": [0.8,0.7,0.4,0.9],
    })


def test_first_interaction_history_is_missing_not_zero():
    out=add_longitudinal_features(sample())
    first=out[out.victim_id=="V1"].iloc[0]
    assert first.has_previous_interaction == 0
    assert np.isnan(first.historical_distress_mean)
    assert np.isnan(first.distress_delta)


def test_dynamic_features_use_past_only():
    out=add_longitudinal_features(sample())
    third=out[(out.victim_id=="V1")&(out.interaction_number==3)].iloc[0]
    assert third.distress_delta == 15
    assert third.historical_distress_mean == 45
    assert third.recent_distress_mean == 45
    assert third.distress_momentum == 25
    assert round(third.fear_change,3)==0.4


def test_trend_labels():
    assert trend_label([40,42,44])=="increasing"
    assert trend_label([40,45,58])=="rapidly increasing"
    assert trend_label([60,56,50])=="improving"
    assert trend_label([50,51,52])=="stable"
