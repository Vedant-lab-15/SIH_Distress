from pathlib import Path
import pandas as pd
import joblib

from ml.data.loader import load_dataset
from ml.features.dynamic import add_longitudinal_features
from ml.inference.predictor import Predictor
from ml.training.split import victim_level_split


ROOT=Path(__file__).resolve().parents[1]


def test_model_predicts_in_bounds():
    model_path=ROOT/"models/dynamic_xgboost.joblib"
    if not model_path.exists():
        return
    df=load_dataset(ROOT/"data/synthetic/synthetic_distress_dataset.csv")
    df=add_longitudinal_features(df)
    _,_,te=victim_level_split(df)
    artifact=joblib.load(model_path)
    x=te.head(1)
    pred=Predictor(model_path).predict_frame(x)[0]
    assert 0 <= pred <= 100
    assert "next_distress_score" not in artifact["feature_names"]
