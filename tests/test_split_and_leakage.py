from pathlib import Path
import pandas as pd

from ml.features.dynamic import add_longitudinal_features
from ml.features.schema import DYNAMIC_FEATURES, TARGET, validate_no_target_leakage
from ml.training.split import victim_level_split


ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/synthetic/synthetic_distress_dataset.csv"


def test_victim_level_split_disjoint():
    df=pd.read_csv(DATA)
    df=add_longitudinal_features(df)
    tr,va,te=victim_level_split(df, seed=42)
    assert set(tr.victim_id).isdisjoint(set(va.victim_id))
    assert set(tr.victim_id).isdisjoint(set(te.victim_id))
    assert set(va.victim_id).isdisjoint(set(te.victim_id))


def test_no_target_leakage():
    validate_no_target_leakage(DYNAMIC_FEATURES)
    assert TARGET not in DYNAMIC_FEATURES
    assert "risk_level" not in DYNAMIC_FEATURES
    assert "intervention_triggered" not in DYNAMIC_FEATURES
