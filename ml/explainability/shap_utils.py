from __future__ import annotations

from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt


def make_shap_outputs(model, X_test_transformed, feature_names, out_dir: str | Path, sample_size: int = 500):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n = min(sample_size, len(X_test_transformed))
    X_sample = X_test_transformed[:n]
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    shap_values = np.asarray(shap_values)

    np.save(out_dir / "shap_values.npy", shap_values)
    np.save(out_dir / "shap_sample.npy", X_sample)

    plt.figure(figsize=(10, 7))
    shap.summary_plot(
        shap_values, X_sample, feature_names=feature_names,
        plot_type="bar", show=False, max_display=20
    )
    plt.tight_layout()
    plt.savefig(out_dir / "shap_bar.png", dpi=160, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 8))
    shap.summary_plot(
        shap_values, X_sample, feature_names=feature_names,
        show=False, max_display=20
    )
    plt.tight_layout()
    plt.savefig(out_dir / "shap_beeswarm.png", dpi=160, bbox_inches="tight")
    plt.close()

    mean_abs = np.abs(shap_values).mean(axis=0)
    top_idx = np.argsort(mean_abs)[::-1][:20]
    importance = [
        {"feature": feature_names[int(i)], "mean_abs_shap": float(mean_abs[int(i)])}
        for i in top_idx
    ]
    (out_dir / "global_importance.json").write_text(
        json.dumps(importance, indent=2), encoding="utf-8"
    )

    return explainer
