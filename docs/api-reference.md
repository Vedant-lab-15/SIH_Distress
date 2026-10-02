# API Reference — SurakshaMind

**Base URL:** `http://localhost:8000`  
**Auth:** Disabled by default (`AUTH_ENABLED=false`). Set `AUTH_ENABLED=true` + `APP_API_KEY=<key>` for production; pass as `X-API-Key: <key>` header.  
**Content-Type:** `application/json`  
**Interactive docs:** `http://localhost:8000/docs`

> All data returned by demo endpoints is synthetic. No real victim data is processed.

---

## System Endpoints

### GET /

Returns the SurakshaMind SPA (index.html).

**Response:** `text/html`

---

### GET /health

Check system availability and model version.

**Response:**
```json
{
  "status": "ok",
  "model_version": "dynamic-xgboost-v1.0",
  "demo_mode": true
}
```

---

## Demo Endpoints

These six endpoints power the jury prototype UI. No trained model is required for `/demo/checkin` — it uses the lightweight keyword + sentiment formula.

---

### POST /demo/checkin

Submit a text check-in and receive a Dynamic Distress Score with top-3 contributing factors and a recommended intervention.

**Request:**
```json
{
  "text": "I am afraid and cannot sleep. There have been threats. I have no money.",
  "language": "en",
  "sentiment_score": -0.6,
  "missed_checkins": 3,
  "case_delay_days": 200
}
```

| Field | Type | Required | Range | Notes |
|---|---|---|---|---|
| `text` | string | ✓ | 1–2000 chars | Check-in message (English or Hindi) |
| `language` | string | — | `"en"` or `"hi"` | Default: `"en"` |
| `sentiment_score` | float | — | −1.0 to 1.0 | −1 = very negative, +1 = very positive |
| `missed_checkins` | int | — | 0–20 | Number of missed check-ins in last 30 days |
| `case_delay_days` | int | — | 0–3650 | Days since last case progress |

**Response:**
```json
{
  "dds": 68.3,
  "risk_level": "high",
  "top_factors": [
    {"factor": "Distress keywords in text", "weight": 0.40, "raw": 0.87, "contribution": 34.7},
    {"factor": "Negative sentiment detected", "weight": 0.25, "raw": 0.80, "contribution": 20.0},
    {"factor": "Prolonged case delay", "weight": 0.20, "raw": 0.55, "contribution": 10.9}
  ],
  "recommended_intervention": "⚠️  Priority counselling session within 24 hours + legal aid follow-up",
  "formula_note": "Prototype heuristic: 40% keywords + 25% sentiment + 15% engagement + 20% case delay",
  "synthetic": true
}
```

**DDS Formula:**
```
DDS = (0.40 × keyword_norm + 0.25 × sentiment_norm + 0.15 × engagement_penalty + 0.20 × context_penalty) × 100
```

**Risk thresholds:**

| Risk | DDS Range |
|---|---|
| Low | < 40 |
| Moderate | 40 – 64.9 |
| High | 65 – 79.9 |
| Critical | ≥ 80 |

---

### GET /demo/dashboard

Returns up to 50 victims sorted by DDS (highest first), with risk level, case stage and last check-in timestamp.

**Response:**
```json
{
  "count": 50,
  "victims": [
    {
      "victim_id": "V00042",
      "state": "Uttar Pradesh",
      "age": 28,
      "gender": "female",
      "offence_type": "rape",
      "case_stage": "trial",
      "dds": 84.2,
      "risk_level": "critical",
      "last_checkin": "2026-09-15T10:22:00",
      "interaction_count": 7,
      "requires_review": true
    }
  ]
}
```

---

### GET /demo/victim/{victim_id}

Full victim detail: 30-interaction timeline, SHAP-style factors for the latest check-in, intervention history, and victim profile.

**Path parameter:** `victim_id` — e.g. `V00001`

**Response:**
```json
{
  "victim": {
    "victim_id": "V00001",
    "state": "Maharashtra",
    "age": 32,
    "gender": "female",
    "social_category": "SC",
    "offence_type": "rape",
    "severity": 5
  },
  "current_stage": "trial",
  "trend": "increasing",
  "total_interactions": 10,
  "timeline": [
    {
      "interaction_number": 1,
      "dds": 52.4,
      "risk_level": "moderate",
      "case_stage": "investigation",
      "channel": "chatbot",
      "timestamp": "2026-01-10T09:00:00",
      "summary": "I feel worried about the upcoming hearing…",
      "threat_received": false,
      "economic_stress": 3,
      "social_support": 3
    }
  ],
  "shap_factors": [
    {"feature": "Text distress keywords", "value": 34.7, "direction": "↑ risk"},
    {"feature": "Threat received", "value": 20.0, "direction": "↑ risk"},
    {"feature": "Negative sentiment", "value": 18.5, "direction": "↑ risk"},
    {"feature": "Economic stress", "value": 12.0, "direction": "↑ risk"},
    {"feature": "Low social support", "value": 9.0, "direction": "↑ risk"}
  ],
  "intervention_history": [
    {
      "date": "2026-09-01T14:00:00",
      "dds": 78.4,
      "risk": "high",
      "action": "⚠️  Priority counselling session within 24 hours + legal aid follow-up",
      "reviewed": false
    }
  ]
}
```

---

### GET /demo/alerts

Returns all review flags (open and acknowledged) sorted by creation time, with notification log and recommended action.

**Response:**
```json
{
  "total": 12,
  "open": 8,
  "alerts": [
    {
      "flag_id": 3,
      "victim_id": "V00042",
      "priority": "critical",
      "status": "open",
      "dds": 84.2,
      "created_at": "2026-09-15T10:22:00",
      "recommended_action": "🚨 Immediate counsellor outreach + police protection order recommended",
      "notification_log": [
        {"channel": "SMS",   "sent_at": "2026-09-15T10:22:00", "status": "delivered"},
        {"channel": "Email", "sent_at": "2026-09-15T10:22:00", "status": "delivered"}
      ]
    }
  ]
}
```

---

### POST /demo/acknowledge

Counsellor acknowledges one or more open flags for a victim. All open flags for that victim are marked `"acknowledged"`. An audit log entry is created.

**Request:**
```json
{
  "victim_id": "V00042",
  "counsellor_note": "Called victim. Referred to district hospital counsellor. Follow-up scheduled."
}
```

**Response:**
```json
{
  "acknowledged": 1,
  "victim_id": "V00042"
}
```

**Error:** `404` if no open flags exist for the victim.

---

### GET /demo/analytics

Aggregate statistics for the district/state/national dashboard view.

**Response:**
```json
{
  "total_victims": 2000,
  "risk_distribution": {"low": 1241, "moderate": 433, "high": 218, "critical": 108},
  "high_risk_count": 326,
  "intervention_success_rate": 75.0,
  "total_alerts": 12,
  "acknowledged_alerts": 9,
  "state_heatmap": [
    {
      "state": "Uttar Pradesh",
      "total_victims": 340,
      "avg_dds": 61.4,
      "high_critical_count": 82,
      "risk_rate": 24.1
    }
  ],
  "case_stage_breakdown": {
    "investigation": 412,
    "trial": 688,
    "compensation": 341,
    "rehabilitation": 559
  },
  "synthetic": true
}
```

---

## Original ML Endpoints

These endpoints use the trained Dynamic XGBoost model and require `models/dynamic_xgboost.joblib` to be present.

### POST /predict

Full ML prediction with SHAP explanations and database persistence.  
See `docs/API.md` for the complete 27-field `InteractionInput` schema.

### POST /batch-predict

Batch version of `/predict`. Body: `{"interactions": [<InteractionInput>, ...]}`

### POST /interaction

Stores a structured interaction record without running prediction.

### GET /victim/{victim_id}

Full victim profile + interaction history + recent predictions from the ML pipeline.

### GET /victim/{victim_id}/timeline

Distress history + trend label for a victim.

### GET /review-queue

Open high/critical ML prediction flags.

### GET /model/info

Model metadata, feature set, risk thresholds.

### GET /model/metrics

Full evaluation results (requires auth in production).

### GET /system-health

Database, model artifact and dataset presence check.

---

## Error Responses

| Code | Meaning |
|---|---|
| `404` | Resource not found (victim, flag, model artifact) |
| `422` | Validation error — request body fails Pydantic schema |
| `401` | Invalid or missing API key (only when `AUTH_ENABLED=true`) |
| `500` | Internal server error — check logs |
| `503` | Model artifact not found — run `python scripts/train_model.py` first |
