# API Documentation

Base URL: `http://localhost:8000`

The API returns model estimates only. It does not diagnose mental illness or initiate autonomous high-impact actions.

## Health

`GET /health`

Returns application and model availability.

## Model information

`GET /model/info`

Returns model version, feature set, target and synthetic benchmark thresholds.

## Metrics

`GET /model/metrics`

Returns the stored regression/classification evaluation results.

## Predict

`POST /predict`

Accepts one current interaction. History already stored for the same `victim_id` is used to compute longitudinal features. A high or critical result is persisted as a human-review flag.

Example:

```json
{
  "victim_id": "V00001",
  "interaction_number": 11,
  "days_since_registration": 300,
  "state": "Maharashtra",
  "age": 30,
  "gender": "female",
  "social_category": "SC",
  "offence_type": "rape",
  "severity_1_to_5": 5,
  "case_stage": "trial",
  "communication_channel": "chatbot",
  "threat_received": 1,
  "investigation_or_court_delay_days": 140,
  "court_appearances_to_date": 5,
  "economic_stress_1_to_5": 4,
  "social_support_1_to_5": 2,
  "relief_status": "pending",
  "counselling_status": "not_provided",
  "text_response": "I am worried about what will happen next.",
  "sentiment_score": -0.25,
  "fear_score": 0.72,
  "sadness_score": 0.65,
  "anger_score": 0.30,
  "voice_stress_score": 0.68,
  "engagement_score": 0.42,
  "current_distress_score": 71.5
}
```

Response:

```json
{
  "predicted_distress_score": 72.4,
  "risk_level": "high",
  "requires_human_review": true,
  "model_version": "dynamic-xgboost-v1.0",
  "trend": "increasing",
  "contributors": [
    {"feature": "current_distress_score", "shap_value": 5.31}
  ]
}
```

## Batch prediction

`POST /batch-predict`

Body: `{"interactions": [<InteractionInput>, ...]}`

## Store interaction

`POST /interaction`

Stores a structured interaction in SQLite/PostgreSQL. This endpoint does not automatically contact any third party.

## Victim

`GET /victim/{victim_id}`

Returns minimal synthetic/demo metadata, interaction timeline and recent predictions.

## Timeline

`GET /victim/{victim_id}/timeline`

Returns current distress history and trend descriptor.

## Latest interaction

`GET /victim/{victim_id}/latest`

Returns the latest stored demo interaction fields used to prefill the browser prediction simulator.

## Human review queue

`GET /review-queue`

Returns open high/critical model review flags.

## System health

`GET /system-health`

Returns database/model/demo health indicators.

## Optional authentication

When `AUTH_ENABLED=true`, protected endpoints require:

`X-API-Key: <APP_API_KEY>`

The demo defaults to disabled authentication for local use. Production deployments should place the API behind an institutional identity/access-control layer rather than relying on a shared static API key.
