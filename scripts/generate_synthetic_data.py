from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd


TEXT_TEMPLATES = [
    "I am worried about what will happen next.",
    "I feel exhausted but I still want to continue.",
    "I need someone to explain what happens next.",
    "I feel safer now that I have received support.",
    "I am finding it hard to sleep and stay focused.",
    "I am managing today, but the process feels difficult.",
    "I feel hopeful when I receive clear updates.",
]


def risk(score):
    if score < 40:
        return "low"
    if score < 65:
        return "moderate"
    if score < 80:
        return "high"
    return "critical"


def generate(n_victims=2000, interactions=10, seed=42):
    rng = np.random.default_rng(seed)
    states = ["Maharashtra", "Telangana", "Karnataka", "Gujarat", "Rajasthan", "Uttar Pradesh"]
    genders = ["female", "male", "other"]
    social = ["SC", "ST", "other"]
    offences = ["rape", "gang_rape", "murder", "grievous_hurt", "arson", "intimidation"]
    stages = ["complaint", "investigation", "charge_sheet", "trial", "appeal", "rehabilitation", "compensation"]
    channels = ["chatbot", "helpline", "SMS", "web_portal", "IVRS", "mobile_app"]
    records = []

    for i in range(1, n_victims + 1):
        victim_id = f"V{i:05d}"
        age = int(np.clip(rng.normal(38, 14), 18, 78))
        gender = rng.choice(genders, p=[0.48, 0.47, 0.05])
        social_category = rng.choice(social, p=[0.48, 0.22, 0.30])
        offence = rng.choice(offences, p=[0.21, 0.07, 0.20, 0.19, 0.15, 0.18])
        severity = int(np.clip(round(rng.normal(3.4, 1.0)), 1, 5))
        latent = float(np.clip(rng.normal(55, 15), 10, 90))
        prior = np.nan
        current = float(np.clip(latent + rng.normal(0, 8), 0, 100))

        day = 0
        for k in range(1, interactions + 1):
            if k > 1:
                day += int(rng.integers(18, 45))
                stage = stages[min(k // 2, len(stages) - 1)]
            else:
                stage = "complaint"

            threat = int(rng.random() < (0.15 + 0.08 * (severity >= 4)))
            delay = int(np.clip(rng.normal(55 + 12*k, 25), 0, 220))
            appearances = int(np.clip(rng.poisson(max(0.3, k/2)), 0, 10))
            econ = int(rng.integers(1, 6))
            support = int(rng.integers(1, 6))
            relief = "received" if rng.random() < min(0.15 + k*0.08, 0.85) else "pending"
            counselling = "provided" if rng.random() < min(0.12 + k*0.05, 0.7) else "not_provided"
            sentiment = float(np.clip(rng.normal(0.15 - 0.009*current + 0.03*support, 0.12), -1, 1))
            fear = float(np.clip(rng.normal(0.18 + 0.006*current + 0.10*threat, 0.15), 0, 1))
            sadness = float(np.clip(rng.normal(0.12 + 0.007*current, 0.16), 0, 1))
            anger = float(np.clip(rng.normal(0.12 + 0.006*current + 0.02*(delay > 100), 0.15), 0, 1))
            voice_stress = float(np.clip(rng.normal(0.20 + 0.006*current + 0.08*threat, 0.14), 0, 1))
            engagement = float(np.clip(rng.normal(0.78 - 0.004*current + 0.04*support, 0.12), 0, 1))
            text = rng.choice(TEXT_TEMPLATES)
            next_score = np.clip(
                current
                + 0.28*(current - (prior if np.isfinite(prior) else current))
                + 5.5*threat
                + 2.0*econ
                - 1.6*support
                + 5.0*voice_stress
                - 3.0*engagement
                + 0.015*delay
                + rng.normal(0, 4.5),
                0, 100
            )
            records.append({
                "victim_id": victim_id,
                "interaction_number": k,
                "days_since_registration": day,
                "state": states[(i + k) % len(states)],
                "age": age,
                "gender": gender,
                "social_category": social_category,
                "offence_type": offence,
                "severity_1_to_5": severity,
                "case_stage": stage,
                "communication_channel": channels[int(rng.integers(0, len(channels)))],
                "threat_received": threat,
                "investigation_or_court_delay_days": delay,
                "court_appearances_to_date": appearances,
                "economic_stress_1_to_5": econ,
                "social_support_1_to_5": support,
                "relief_status": relief,
                "counselling_status": counselling,
                "text_response": text,
                "sentiment_score": sentiment,
                "fear_score": fear,
                "sadness_score": sadness,
                "anger_score": anger,
                "voice_stress_score": voice_stress,
                "engagement_score": engagement,
                "previous_distress_score": float(prior) if np.isfinite(prior) else np.nan,
                "current_distress_score": float(current),
                "next_distress_score": float(next_score),
                "risk_level": risk(float(next_score)),
                "intervention_triggered": "yes" if next_score >= 65 else "no",
            })
            prior = current
            current = float(next_score)

    return pd.DataFrame(records)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--victims", type=int, default=2000)
    p.add_argument("--interactions", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", default="data/synthetic/synthetic_distress_dataset_generated.csv")
    args = p.parse_args()

    df = generate(args.victims, args.interactions, args.seed)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Generated {len(df):,} synthetic records -> {out}")
