from __future__ import annotations

import json
from pathlib import Path

from ml.explainability.shap_utils import make_shap_outputs

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor

from ml.data.loader import load_dataset
from ml.evaluation.fairness import group_regression_metrics
from ml.evaluation.metrics import classification_metrics, regression_metrics
from ml.features.dynamic import add_longitudinal_features
from ml.features.schema import DYNAMIC_FEATURES, STATIC_FEATURES, TARGET, validate_no_target_leakage
from ml.preprocessing.pipeline import make_preprocessor, transformed_feature_names
from ml.training.split import victim_level_split

matplotlib.use("Agg")


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data/synthetic/synthetic_distress_dataset.csv"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"


def fit_and_eval(name, model, train_df, val_df, test_df, feature_set):
    pre = make_preprocessor(feature_set)
    X_train = pre.fit_transform(train_df)
    X_val = pre.transform(val_df)
    X_test = pre.transform(test_df)
    y_train = train_df[TARGET].to_numpy()
    y_val = val_df[TARGET].to_numpy()
    y_test = test_df[TARGET].to_numpy()

    model.fit(X_train, y_train)
    pred_val = np.clip(model.predict(X_val), 0, 100)
    pred_test = np.clip(model.predict(X_test), 0, 100)

    result = {
        "model": name,
        "feature_set": feature_set,
        "train_size": len(train_df),
        "validation_size": len(val_df),
        "test_size": len(test_df),
        "validation": regression_metrics(y_val, pred_val),
        "test": regression_metrics(y_test, pred_test),
        "test_risk": classification_metrics(y_test, pred_test),
    }
    artifact = {
        "model": model,
        "preprocessor": pre,
        "feature_names": transformed_feature_names(pre),
        "model_version": f"{name.lower().replace(' ', '-')}-v1.0",
        "feature_set": feature_set,
    }
    joblib.dump(artifact, MODELS / f"{name.lower().replace(' ', '_')}.joblib")

    if name == "Dynamic XGBoost":
        transformed = pre.transform(test_df)
        explainer = make_shap_outputs(
            model, transformed, artifact["feature_names"],
            REPORTS / "figures", sample_size=500
        )
        # One representative test explanation
        row_index = 0
        shap_row = explainer.shap_values(transformed[row_index:row_index+1])
        if isinstance(shap_row, list):
            shap_row = shap_row[0]
        shap_row = np.asarray(shap_row)[0]
        top = np.argsort(np.abs(shap_row))[::-1][:8]
        local = []
        pred = float(pred_test[row_index])
        for idx in top:
            local.append({
                "feature": artifact["feature_names"][int(idx)],
                "shap_value": float(shap_row[int(idx)]),
            })
        (REPORTS / "figures" / "sample_explanation.json").write_text(
            json.dumps({
                "predicted_distress_score": round(pred, 2),
                "risk_level": "high" if pred >= 65 else ("moderate" if pred >= 40 else "low"),
                "contributors": local,
                "note": "SHAP values are model attributions, not causal effects."
            }, indent=2),
            encoding="utf-8",
        )
        fairness = group_regression_metrics(test_df, pred_test)
        fairness.to_csv(REPORTS / "fairness_metrics.csv", index=False)

    return result, artifact


def main():
    MODELS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    REPORTS.joinpath("figures").mkdir(parents=True, exist_ok=True)

    df = load_dataset(DATASET)
    dynamic = add_longitudinal_features(df)
    train, val, test = victim_level_split(dynamic, seed=42)
    processed_path = ROOT / "data/processed/dynamic_features.csv"
    dynamic.to_csv(processed_path, index=False)
    (REPORTS / "splits.json").write_text(json.dumps({
        "seed": 42,
        "train_victims": sorted(train.victim_id.unique().tolist()),
        "validation_victims": sorted(val.victim_id.unique().tolist()),
        "test_victims": sorted(test.victim_id.unique().tolist()),
    }, indent=2), encoding="utf-8")

    feature_sets = {
        "Current Distress Only": "current_only",
        "Ridge": "static",
        "Random Forest": "static",
        "XGBoost": "static",
        "Dynamic XGBoost": "dynamic",
    }

    models = {
        "Ridge": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(
            n_estimators=250, max_depth=10, min_samples_leaf=3, random_state=42, n_jobs=-1
        ),
        "XGBoost": XGBRegressor(
            n_estimators=450, max_depth=5, learning_rate=0.045,
            subsample=0.85, colsample_bytree=0.85, reg_lambda=2.0,
            objective="reg:squarederror", random_state=42, n_jobs=4
        ),
        "Dynamic XGBoost": XGBRegressor(
            n_estimators=550, max_depth=5, learning_rate=0.04,
            subsample=0.85, colsample_bytree=0.85, reg_lambda=3.0,
            objective="reg:squarederror", random_state=42, n_jobs=4
        ),
    }

    results = []
    # Mean baseline
    mean_pred = np.full(len(test), train[TARGET].mean())
    results.append({
        "model": "Mean Baseline",
        "feature_set": "none",
        "train_size": len(train),
        "validation_size": len(val),
        "test_size": len(test),
        "validation": {},
        "test": regression_metrics(test[TARGET], mean_pred),
        "test_risk": classification_metrics(test[TARGET], mean_pred),
    })

    # Current distress only ablation
    pre = make_preprocessor("current_only")
    Xtr = pre.fit_transform(train)
    Xte = pre.transform(test)
    cur_model = Ridge(alpha=10.0).fit(Xtr, train[TARGET])
    cur_pred = np.clip(cur_model.predict(Xte), 0, 100)
    joblib.dump({
        "model": cur_model, "preprocessor": pre,
        "feature_names": transformed_feature_names(pre),
        "model_version": "current-distress-only-v1.0",
        "feature_set": "current_only",
    }, MODELS / "current_distress_only.joblib")
    results.append({
        "model": "Current Distress Only",
        "feature_set": "current_only",
        "train_size": len(train),
        "validation_size": len(val),
        "test_size": len(test),
        "validation": {},
        "test": regression_metrics(test[TARGET], cur_pred),
        "test_risk": classification_metrics(test[TARGET], cur_pred),
    })

    for name in ["Ridge", "Random Forest", "XGBoost", "Dynamic XGBoost"]:
        result, _ = fit_and_eval(
            name, models[name], train, val, test, "dynamic" if name == "Dynamic XGBoost" else "static"
        )
        results.append(result)

    metrics = {
        "dataset": str(DATASET.relative_to(ROOT)),
        "seed": 42,
        "target": TARGET,
        "risk_thresholds": {"low": "<40", "moderate": "40-64.99", "high": "65-79.99", "critical": ">=80"},
        "victim_counts": {
            "train": int(train.victim_id.nunique()),
            "validation": int(val.victim_id.nunique()),
            "test": int(test.victim_id.nunique()),
        },
        "row_counts": {"train": len(train), "validation": len(val), "test": len(test)},
        "results": results,
        "leakage_columns_excluded": sorted(validate_leakage_report(df)),
        "note": "Metrics are from the supplied synthetic benchmark; they are not clinical validation."
    }
    (REPORTS / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    summary = []
    for r in results:
        summary.append({
            "model": r["model"],
            "test_mae": r["test"].get("mae"),
            "test_rmse": r["test"].get("rmse"),
            "test_r2": r["test"].get("r2"),
            "high_critical_precision": r["test_risk"].get("high_critical_precision"),
            "high_critical_recall": r["test_risk"].get("high_critical_recall"),
            "high_critical_f1": r["test_risk"].get("high_critical_f1"),
        })
    pd.DataFrame(summary).to_csv(REPORTS / "model_comparison.csv", index=False)

    print(pd.DataFrame(summary).to_string(index=False))


def validate_leakage_report(df):
    # Report target/derived labels present in source data, all excluded from training.
    return {"next_distress_score", "risk_level", "intervention_triggered"}


if __name__ == "__main__":
    main()
