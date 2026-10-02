# Evaluation Results

**Benchmark:** supplied synthetic dataset (20,000 interactions; 2,000 synthetic victims)

**Split:** 70% victims train / 15% validation / 15% test; no victim overlap.

| Model | Test MAE | Test RMSE | Test R² | High+Critical Precision | High+Critical Recall | High+Critical F1 |
|---|---:|---:|---:|---:|---:|---:|
| Mean Baseline | 20.7886 | 25.5924 | -0.0039 | 0.0000 | 0.0000 | 0.0000 |
| Current Distress Only | 8.0965 | 10.3969 | 0.8343 | 0.8538 | 0.7669 | 0.8080 |
| Ridge | 4.7609 | 6.0197 | 0.9445 | 0.9310 | 0.8462 | 0.8865 |
| Random Forest | 5.4431 | 6.8934 | 0.9272 | 0.8916 | 0.8367 | 0.8632 |
| XGBoost | 4.8382 | 6.1113 | 0.9428 | 0.9056 | 0.8627 | 0.8836 |
| Dynamic XGBoost | 4.8227 | 6.1106 | 0.9428 | 0.9048 | 0.8663 | 0.8851 |

## Ablation

The current-distress-only baseline achieves MAE **8.0965**, RMSE **10.3969**, R² **0.8343**. The Dynamic XGBoost model achieves MAE **4.8227**, RMSE **6.1106**, R² **0.9428**.

This indicates that, on this synthetic benchmark, the additional structured and longitudinal signals contain predictive information beyond the current distress score alone. It does not establish clinical usefulness.

## Model choice for the deployable demo

Ridge has slightly better regression metrics on this held-out synthetic test set (MAE 4.7609; RMSE 6.0197; R² 0.9445). Dynamic XGBoost has slightly higher combined high+critical recall (0.8663 vs 0.8462 for Ridge) while retaining similar regression performance, and it supports nonlinear SHAP explanations. The demo therefore packages Dynamic XGBoost as the reference model while preserving the comparison results.

This is a benchmark engineering choice, not evidence that the model is clinically superior.

## Fairness / group analysis

See `reports/fairness_metrics.csv`. Metrics are reported for synthetic groups with at least 50 test records. Differences are preserved rather than hidden; they should be treated as signals for further model investigation.

## Interpretation

SHAP feature importance is model attribution and is not causal evidence. `current_distress_score` is the dominant feature in this run, followed by economic stress, social support and court-appearance history.

## Limitations

All benchmark records are synthetic. These metrics must not be interpreted as clinical validation, public-service validation, or evidence of real-world accuracy.
