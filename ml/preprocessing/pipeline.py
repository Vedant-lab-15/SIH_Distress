from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.features.schema import (
    CATEGORICAL_FEATURES,
    DYNAMIC_FEATURES,
    RAW_NUMERIC_FEATURES,
    STATIC_FEATURES,
    validate_no_target_leakage,
)


def make_preprocessor(feature_set: str = "dynamic") -> ColumnTransformer:
    if feature_set == "dynamic":
        features = DYNAMIC_FEATURES
        numeric = RAW_NUMERIC_FEATURES + [
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
    elif feature_set == "static":
        features = STATIC_FEATURES
        numeric = RAW_NUMERIC_FEATURES
    elif feature_set == "current_only":
        features = ["current_distress_score"]
        numeric = ["current_distress_score"]
    else:
        raise ValueError(f"Unknown feature_set={feature_set!r}")

    validate_no_target_leakage(features)

    categorical = [c for c in CATEGORICAL_FEATURES if c in features]
    numeric = [c for c in numeric if c in features]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric),
            ("cat", categorical_pipeline, categorical),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def transformed_feature_names(preprocessor: ColumnTransformer) -> list[str]:
    return list(preprocessor.get_feature_names_out())
