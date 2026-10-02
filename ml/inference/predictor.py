from __future__ import annotations

from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from ml.evaluation.metrics import risk_from_score


class Predictor:
    def __init__(self, artifact_path: str | Path):
        artifact = joblib.load(artifact_path)
        self.model = artifact["model"]
        self.preprocessor = artifact["preprocessor"]
        self.feature_names = artifact["feature_names"]
        self.model_version = artifact["model_version"]

    def predict_frame(self, features: pd.DataFrame) -> np.ndarray:
        X = self.preprocessor.transform(features)
        pred = self.model.predict(X)
        return np.clip(np.asarray(pred, dtype=float), 0, 100)

    def predict_one(self, features: pd.DataFrame) -> dict:
        score = float(self.predict_frame(features)[0])
        risk = risk_from_score(score)
        return {
            "predicted_distress_score": round(score, 2),
            "risk_level": risk,
            "requires_human_review": risk in {"high", "critical"},
            "model_version": self.model_version,
        }
