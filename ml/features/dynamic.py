from __future__ import annotations

import numpy as np
import pandas as pd

from ml.features.schema import DYNAMIC_NUMERIC_FEATURES


def add_longitudinal_features(df: pd.DataFrame) -> pd.DataFrame:
    required = {"victim_id", "interaction_number", "current_distress_score",
                "fear_score", "sadness_score", "voice_stress_score", "engagement_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for longitudinal feature engineering: {sorted(missing)}")

    out = df.copy()
    out = out.sort_values(["victim_id", "interaction_number"]).reset_index(drop=True)

    grouped = out.groupby("victim_id", sort=False)

    prev_distress = grouped["current_distress_score"].shift(1)
    prev2_distress = grouped["current_distress_score"].shift(2)

    out["has_previous_interaction"] = prev_distress.notna().astype(float)
    out["distress_delta"] = out["current_distress_score"] - prev_distress
    out["historical_distress_mean"] = (
        grouped["current_distress_score"]
        .transform(lambda s: s.shift(1).expanding(min_periods=1).mean())
    )
    out["recent_distress_mean"] = (
        grouped["current_distress_score"]
        .transform(lambda s: s.shift(1).rolling(window=3, min_periods=1).mean())
    )
    out["distress_momentum"] = out["current_distress_score"] - prev2_distress

    for col in ["fear_score", "sadness_score", "voice_stress_score", "engagement_score"]:
        out[f"{col.replace('_score', '')}_change"] = (
            out[col] - grouped[col].shift(1)
        )

    # First interaction deliberately retains NaN for history-based measures.
    # Downstream preprocessing uses median imputation + missing indicators.
    return out


def add_single_interaction_features(
    row: pd.DataFrame,
    history: pd.DataFrame | None = None,
) -> pd.DataFrame:
    base = row.copy()
    if history is None or history.empty:
        history = pd.DataFrame(columns=base.columns)

    history = history.sort_values("interaction_number")
    prior = history.tail(1)

    def prior_value(col: str):
        return prior[col].iloc[0] if not prior.empty and col in prior.columns else np.nan

    prior2 = history.tail(2)
    prior2_value = (
        prior2["current_distress_score"].iloc[0]
        if len(prior2) >= 2 else np.nan
    )

    current = float(base["current_distress_score"].iloc[0])

    base["has_previous_interaction"] = 1.0 if not prior.empty else 0.0
    base["distress_delta"] = current - prior_value("current_distress_score") if not prior.empty else np.nan
    base["historical_distress_mean"] = (
        float(history["current_distress_score"].mean()) if not history.empty else np.nan
    )
    base["recent_distress_mean"] = (
        float(history["current_distress_score"].tail(3).mean()) if not history.empty else np.nan
    )
    base["distress_momentum"] = (
        current - prior2_value if len(prior2) >= 2 else np.nan
    )

    for col in ["fear_score", "sadness_score", "voice_stress_score", "engagement_score"]:
        base[f"{col.replace('_score', '')}_change"] = (
            float(base[col].iloc[0]) - prior_value(col) if not prior.empty else np.nan
        )
    return base


def trend_label(scores: list[float] | np.ndarray) -> str:
    vals = np.asarray(scores, dtype=float)
    vals = vals[np.isfinite(vals)]
    if len(vals) < 2:
        return "stable"
    recent = vals[-3:] if len(vals) >= 3 else vals
    delta = recent[-1] - recent[0]
    if delta >= 12:
        return "rapidly increasing"
    if delta >= 4:
        return "increasing"
    if delta <= -4:
        return "improving"
    return "stable"
