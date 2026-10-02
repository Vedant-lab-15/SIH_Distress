# Reproducibility

The training run uses seed `42`.

Run:

```bash
python scripts/prepare_data.py
python scripts/train_model.py
python scripts/evaluate.py
```

The pipeline creates:

- `data/processed/dynamic_features.csv`
- `reports/splits.json`
- `reports/metrics.json`
- `reports/model_comparison.csv`
- `reports/fairness_metrics.csv`
- `reports/figures/*`
- `models/*.joblib`

The victim-level split is asserted in both the code and tests. Because the source benchmark itself is synthetic, reproducibility does not imply real-world validity.
