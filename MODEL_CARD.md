# Model Card — Dynamic Distress XGBoost

## Model purpose

Predict the next synthetic distress score (0–100) from information available at the current interaction and longitudinal history.

## Intended use

Software prototype / research demonstration of longitudinal predictive modeling, explainability and human-review workflows.

## Prohibited use

Do not use this artifact to diagnose mental illness, determine medical treatment, make legal findings, contact police/family automatically, deny benefits, change case status, or make other high-impact decisions.

## Data

The benchmark is synthetic and contains 20,000 records from 2,000 synthetic victims. No real victim records are included in the repository.

## Target

`next_distress_score` on a 0–100 scale.

## Features

Structured case/demographic/interaction variables plus longitudinal features:

- distress delta
- historical distress mean
- recent distress mean
- distress momentum
- changes in fear, sadness, voice-stress and engagement
- previous-interaction indicator

Raw target and derived labels are excluded from training.

## Evaluation

The data is split by victim ID into 70% train / 15% validation / 15% test. Assertions verify that no victim ID occurs in more than one partition.

See `reports/metrics.json` and `reports/model_comparison.csv` for the run generated in this environment.

On the held-out synthetic test set, Dynamic XGBoost achieved:
- MAE: 4.8227
- RMSE: 6.1106
- R²: 0.9428
- High+Critical precision: 0.9048
- High+Critical recall: 0.8663
- High+Critical F1: 0.8851

The current-distress-only ablation achieved MAE 8.0965, RMSE 10.3969 and R² 0.8343.


## Limitations

- Synthetic data is not representative clinical evidence.
- Performance depends on synthetic generation assumptions.
- Voice stress is a feature proxy; no real audio is processed.
- Text is retained for future NLP extensions but the core deployable model is structured/dynamic.
- Model outputs represent statistical estimates, not diagnoses or causal conclusions.
- Formal clinical, legal, security and privacy review is required before any real-world deployment.

## Explainability

SHAP global and local attributions are generated for the Dynamic XGBoost model. SHAP is an attribution method and does not prove causality.

## Fairness

Group metrics are computed for selected synthetic groups where sample size permits. Disparities in synthetic data should be treated as diagnostic signals for further investigation, not evidence about real populations.

## Human oversight

High and critical predictions generate `HUMAN REVIEW REQUIRED` flags. Human reviewers remain responsible for all actions.

## Version

`dynamic-xgb-v1.0`
