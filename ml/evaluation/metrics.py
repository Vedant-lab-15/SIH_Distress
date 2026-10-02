from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)


def risk_from_score(score: float) -> str:
    if score < 40:
        return "low"
    if score < 65:
        return "moderate"
    if score < 80:
        return "high"
    return "critical"


def risk_series(scores) -> list[str]:
    return [risk_from_score(float(s)) for s in scores]


def regression_metrics(y_true, y_pred) -> dict:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def classification_metrics(y_true, y_pred) -> dict:
    true_risk = risk_series(y_true)
    pred_risk = risk_series(y_pred)
    labels = ["low", "moderate", "high", "critical"]
    cm = confusion_matrix(true_risk, pred_risk, labels=labels)
    high_critical_true = np.isin(true_risk, ["high", "critical"])
    high_critical_pred = np.isin(pred_risk, ["high", "critical"])
    return {
        "accuracy": float(accuracy_score(true_risk, pred_risk)),
        "precision_macro": float(precision_score(true_risk, pred_risk, labels=labels, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(true_risk, pred_risk, labels=labels, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(true_risk, pred_risk, labels=labels, average="macro", zero_division=0)),
        "high_critical_precision": float(precision_score(high_critical_true, high_critical_pred, zero_division=0)),
        "high_critical_recall": float(recall_score(high_critical_true, high_critical_pred, zero_division=0)),
        "high_critical_f1": float(f1_score(high_critical_true, high_critical_pred, zero_division=0)),
        "confusion_matrix": cm.tolist(),
        "confusion_labels": labels,
    }
