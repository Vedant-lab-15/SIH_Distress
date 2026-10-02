# Synthetic Data Dictionary

**Dataset label: SYNTHETIC — NOT REAL VICTIM DATA**

The supplied benchmark contains 20,000 interaction records from 2,000 synthetic victim IDs, with 10 longitudinal interactions per victim. These records are suitable for demonstrating software and ML pipeline mechanics only.

| Field | Type | Meaning |
|---|---|---|
| victim_id | string | Synthetic victim identifier. |
| interaction_number | integer | Longitudinal interaction index starting at 1. |
| days_since_registration | integer | Synthetic elapsed days since registration. |
| state | categorical | Synthetic state category used for benchmark grouping. |
| age | integer | Synthetic age in years. |
| gender | categorical | Synthetic gender category. |
| social_category | categorical | Synthetic social category. |
| offence_type | categorical | Synthetic offence category. |
| severity_1_to_5 | integer | Synthetic case-severity score. |
| case_stage | categorical | Synthetic case stage. |
| communication_channel | categorical | Synthetic interaction channel. |
| threat_received | binary | Synthetic indicator for reported threat in the interaction. |
| investigation_or_court_delay_days | integer | Synthetic delay measure. |
| court_appearances_to_date | integer | Synthetic cumulative appearances. |
| economic_stress_1_to_5 | integer | Synthetic economic-stress feature. |
| social_support_1_to_5 | integer | Synthetic perceived social-support feature. |
| relief_status | categorical | Synthetic relief status. |
| counselling_status | categorical | Synthetic counselling-status feature. |
| text_response | string | Synthetic interaction text. |
| sentiment_score | float | Synthetic sentiment feature on approximately -1 to 1. |
| fear_score | float | Synthetic normalized fear indicator 0 to 1. |
| sadness_score | float | Synthetic normalized sadness indicator 0 to 1. |
| anger_score | float | Synthetic normalized anger indicator 0 to 1. |
| voice_stress_score | float | Synthetic speech-stress proxy 0 to 1; no voice recordings are included. |
| engagement_score | float | Synthetic engagement indicator 0 to 1. |
| previous_distress_score | float | Source-column historical score. The production feature builder derives history from prior rows instead of blindly trusting this value. |
| current_distress_score | float | Current synthetic distress score 0–100. |
| next_distress_score | float | Prediction target: next synthetic distress score 0–100. |
| risk_level | categorical | Synthetic label derived from next distress using project thresholds; excluded from model inputs. |
| intervention_triggered | categorical | Synthetic demonstration field; excluded from model inputs. |

## Synthetic threshold mapping

- low: `< 40`
- moderate: `40–64.99`
- high: `65–79.99`
- critical: `>= 80`

These are project-specific benchmark thresholds and are **not clinical thresholds**.
