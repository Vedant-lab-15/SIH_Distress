from __future__ import annotations

import pandas as pd
import numpy as np
from ml.evaluation.metrics import regression_metrics


def group_regression_metrics(df: pd.DataFrame, y_pred, group_cols=None, min_n=50):
    if group_cols is None:
        group_cols = ["gender", "social_category", "offence_type", "age_group"]
    work = df.copy()
    work["prediction"] = np.asarray(y_pred)
    work["age_group"] = pd.cut(
        work["age"], bins=[0, 17, 29, 44, 59, 120],
        labels=["0-17", "18-29", "30-44", "45-59", "60+"],
        right=True,
    )
    rows = []
    for col in group_cols:
        for value, g in work.groupby(col, observed=True):
            if len(g) >= min_n:
                m = regression_metrics(g["next_distress_score"], g["prediction"])
                rows.append({"group": col, "value": str(value), "n": int(len(g)), **m})
    return pd.DataFrame(rows)
