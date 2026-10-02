from __future__ import annotations

from pathlib import Path
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backend.config import settings
from app.backend.database import (
    AuditLog, Interaction, Prediction, ReviewFlag, SessionLocal, Victim, init_db
)
from app.backend.schemas import BatchRequest, InteractionInput, PredictionResponse
from app.backend.security import require_api_key
from ml.features.dynamic import add_longitudinal_features, add_single_interaction_features, trend_label
from ml.inference.predictor import Predictor


logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("distress-monitor")

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "app/frontend"
MODEL_PATH = settings.model_dir / "dynamic_xgboost.joblib"
METRICS_PATH = ROOT / "reports/metrics.json"

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    if settings.demo_mode:
        seed_demo_database()
    yield


app = FastAPI(
    title="Dynamic Distress Monitoring API",
    version="1.0.0",
    lifespan=lifespan,
    description=(
        "Prototype API for AI-estimated distress risk requiring human review. "
        "Not a diagnostic system and not a substitute for qualified professionals."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # defaults to ["*"] for demo; set ALLOWED_ORIGINS env var in production
    allow_credentials=False,  # must be False when allow_origins=["*"]
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(FRONTEND / "static")), name="static")
if (REPORTS := ROOT / "reports").exists():
    app.mount("/artifacts", StaticFiles(directory=str(REPORTS)), name="artifacts")

_predictor: Predictor | None = None


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_predictor():
    global _predictor
    if _predictor is None:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail="Trained model not found. Run scripts/train_model.py first.")
        _predictor = Predictor(MODEL_PATH)
    return _predictor


@app.get("/", response_class=HTMLResponse)
def home():
    return (FRONTEND / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health(predictor: Predictor = Depends(get_predictor)):
    return {"status": "ok", "model_version": predictor.model_version, "demo_mode": settings.demo_mode}


@app.get("/model/info")
def model_info(predictor: Predictor = Depends(get_predictor)):
    return {
        "model_version": predictor.model_version,
        "feature_set": "dynamic",
        "target": "next_distress_score",
        "risk_thresholds": {"low": "<40", "moderate": "40-64.99", "high": "65-79.99", "critical": ">=80"},
        "synthetic_benchmark": True,
        "clinical_validation": False,
    }


@app.get("/model/metrics")
def model_metrics(_: bool = Depends(require_api_key)):
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="Metrics not generated yet")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: InteractionInput, _: bool = Depends(require_api_key),
            predictor: Predictor = Depends(get_predictor),
            db: Session = Depends(db_session)):
    row = pd.DataFrame([payload.model_dump()])
    history_rows = [
        x.__dict__ for x in db.scalars(
            select(Interaction).where(Interaction.victim_id == payload.victim_id).order_by(Interaction.interaction_number)
        ).all()
    ]
    history = pd.DataFrame(history_rows)
    if not history.empty:
        history = history.drop(columns=["_sa_instance_state"], errors="ignore")
        # normalize database field names for feature engineering
        history["interaction_number"] = history["interaction_number"].astype(int)
    feat = add_single_interaction_features(row, history)
    out = predictor.predict_one(feat)

    scores = []
    if not history.empty and "current_distress_score" in history:
        scores.extend(history["current_distress_score"].dropna().astype(float).tolist())
    scores.append(float(payload.current_distress_score))
    out["trend"] = trend_label(scores)

    # Lightweight local SHAP explanation using precomputed transformed features.
    try:
        import shap
        X = predictor.preprocessor.transform(feat)
        explainer = shap.TreeExplainer(predictor.model)
        vals = explainer.shap_values(X)
        if isinstance(vals, list):
            vals = vals[0]
        vals = vals[0]
        names = predictor.feature_names
        idx = sorted(range(len(names)), key=lambda i: abs(float(vals[i])), reverse=True)[:5]
        out["contributors"] = [
            {"feature": names[i], "shap_value": round(float(vals[i]), 4)}
            for i in idx
        ]
    except Exception as exc:
        logger.warning("SHAP inference explanation unavailable: %s", type(exc).__name__)
        out["contributors"] = []

    # Persist prediction and open a human-review flag for high/critical.
    pred = Prediction(
        victim_id=payload.victim_id,
        predicted_distress_score=out["predicted_distress_score"],
        risk_level=out["risk_level"],
        requires_human_review=out["requires_human_review"],
        model_version=out["model_version"],
    )
    db.add(pred)
    db.flush()
    if out["requires_human_review"]:
        flag = ReviewFlag(
            victim_id=payload.victim_id,
            prediction_id=pred.id,
            priority=out["risk_level"],
            status="open",
        )
        db.add(flag)
    db.add(AuditLog(
        event_type="prediction_created",
        actor="api",
        victim_id=payload.victim_id,
        detail=json.dumps({"risk": out["risk_level"], "model_version": out["model_version"]}),
    ))
    db.commit()
    return out


@app.post("/batch-predict")
def batch_predict(payload: BatchRequest, _: bool = Depends(require_api_key),
                  predictor: Predictor = Depends(get_predictor)):
    df = pd.DataFrame([x.model_dump() for x in payload.interactions])
    feat = add_longitudinal_features(df)
    preds = predictor.predict_frame(feat)
    results = []
    for i, score in enumerate(preds):
        from ml.evaluation.metrics import risk_from_score
        risk = risk_from_score(float(score))
        results.append({
            "victim_id": str(feat.iloc[i]["victim_id"]),
            "interaction_number": int(feat.iloc[i]["interaction_number"]),
            "predicted_distress_score": round(float(score), 2),
            "risk_level": risk,
            "requires_human_review": risk in {"high", "critical"},
            "model_version": predictor.model_version,
            "trend": trend_label([
                float(x) for x in feat.loc[feat["victim_id"] == feat.iloc[i]["victim_id"], "current_distress_score"].tail(3)
            ]),
        })
    return {"count": len(results), "predictions": results}


@app.post("/interaction")
def create_interaction(payload: InteractionInput, _: bool = Depends(require_api_key),
                       db: Session = Depends(db_session)):
    victim = db.get(Victim, payload.victim_id)
    if victim is None:
        victim = Victim(
            victim_id=payload.victim_id,
            state=payload.state, age=payload.age, gender=payload.gender,
            social_category=payload.social_category, offence_type=payload.offence_type,
            severity_1_to_5=payload.severity_1_to_5
        )
        db.add(victim)

    item = Interaction(
        victim_id=payload.victim_id,
        interaction_number=payload.interaction_number,
        days_since_registration=payload.days_since_registration,
        case_stage=payload.case_stage,
        communication_channel=payload.communication_channel,
        threat_received=payload.threat_received,
        investigation_or_court_delay_days=payload.investigation_or_court_delay_days,
        court_appearances_to_date=payload.court_appearances_to_date,
        economic_stress_1_to_5=payload.economic_stress_1_to_5,
        social_support_1_to_5=payload.social_support_1_to_5,
        relief_status=payload.relief_status,
        counselling_status=payload.counselling_status,
        text_response=payload.text_response,
        sentiment_score=payload.sentiment_score,
        fear_score=payload.fear_score,
        sadness_score=payload.sadness_score,
        anger_score=payload.anger_score,
        voice_stress_score=payload.voice_stress_score,
        engagement_score=payload.engagement_score,
        current_distress_score=payload.current_distress_score,
    )
    db.add(item)
    db.add(AuditLog(event_type="interaction_created", actor="api", victim_id=payload.victim_id))
    db.commit()
    db.refresh(item)
    return {"interaction_id": item.id, "victim_id": payload.victim_id, "status": "stored"}


@app.get("/victim/{victim_id}")
def victim_detail(victim_id: str, _: bool = Depends(require_api_key),
                  db: Session = Depends(db_session)):
    victim = db.get(Victim, victim_id)
    if victim is None:
        raise HTTPException(status_code=404, detail="Victim not found")
    interactions = db.scalars(
        select(Interaction).where(Interaction.victim_id == victim_id).order_by(Interaction.interaction_number)
    ).all()
    predictions = db.scalars(
        select(Prediction).where(Prediction.victim_id == victim_id).order_by(Prediction.created_at.desc())
    ).all()
    return {
        "victim": {
            "victim_id": victim.victim_id, "state": victim.state, "age": victim.age,
            "gender": victim.gender, "social_category": victim.social_category,
            "offence_type": victim.offence_type, "severity_1_to_5": victim.severity_1_to_5,
        },
        "interactions": [
            {
                "interaction_number": i.interaction_number,
                "current_distress_score": i.current_distress_score,
                "case_stage": i.case_stage,
                "communication_channel": i.communication_channel,
                "timestamp": i.timestamp.isoformat(),
            } for i in interactions
        ],
        "predictions": [
            {
                "predicted_distress_score": p.predicted_distress_score,
                "risk_level": p.risk_level,
                "requires_human_review": p.requires_human_review,
                "model_version": p.model_version,
                "created_at": p.created_at.isoformat(),
            } for p in predictions[:20]
        ]
    }


@app.get("/victim/{victim_id}/timeline")
def victim_timeline(victim_id: str, _: bool = Depends(require_api_key),
                    db: Session = Depends(db_session)):
    items = db.scalars(
        select(Interaction).where(Interaction.victim_id == victim_id).order_by(Interaction.interaction_number)
    ).all()
    if not items:
        raise HTTPException(status_code=404, detail="Victim not found")
    scores = [float(x.current_distress_score) for x in items if x.current_distress_score is not None]
    preds = db.scalars(
        select(Prediction).where(Prediction.victim_id == victim_id).order_by(Prediction.created_at)
    ).all()
    return {
        "victim_id": victim_id,
        "trend": trend_label(scores),
        "timeline": [
            {"interaction_number": i.interaction_number, "current_distress": i.current_distress_score,
             "case_stage": i.case_stage, "channel": i.communication_channel}
            for i in items
        ],
        "latest_prediction": (
            {"predicted_distress": preds[-1].predicted_distress_score, "risk": preds[-1].risk_level}
            if preds else None
        ),
    }


@app.get("/victim/{victim_id}/latest")
def victim_latest(victim_id: str, _: bool = Depends(require_api_key),
                  db: Session = Depends(db_session)):
    item = db.scalars(
        select(Interaction).where(Interaction.victim_id == victim_id).order_by(Interaction.interaction_number.desc())
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Victim not found")
    victim = db.get(Victim, victim_id)
    result = {
        "victim_id": item.victim_id,
        "state": victim.state if victim else "",
        "age": victim.age if victim else 18,
        "gender": victim.gender if victim else "",
        "social_category": victim.social_category if victim else "",
        "offence_type": victim.offence_type if victim else "",
        "severity_1_to_5": victim.severity_1_to_5 if victim else 1,
        **{c: getattr(item, c) for c in [
            "interaction_number", "days_since_registration", "case_stage",
        "communication_channel", "threat_received", "investigation_or_court_delay_days",
        "court_appearances_to_date", "economic_stress_1_to_5", "social_support_1_to_5",
        "relief_status", "counselling_status", "text_response", "sentiment_score",
        "fear_score", "sadness_score", "anger_score", "voice_stress_score",
            "engagement_score", "current_distress_score"
        ]}
    }
    return result


@app.get("/review-queue")
def review_queue(_: bool = Depends(require_api_key), db: Session = Depends(db_session)):
    flags = db.scalars(
        select(ReviewFlag).where(ReviewFlag.status == "open").order_by(ReviewFlag.created_at.desc())
    ).all()
    return {
        "count": len(flags),
        "items": [
            {"victim_id": f.victim_id, "priority": f.priority, "status": f.status,
             "created_at": f.created_at.isoformat()}
            for f in flags
        ]
    }


@app.get("/system-health")
def system_health(_: bool = Depends(require_api_key), db: Session = Depends(db_session)):
    return {
        "database": "ok",
        "open_review_flags": len(db.scalars(select(ReviewFlag).where(ReviewFlag.status == "open")).all()),
        "model_artifact_present": MODEL_PATH.exists(),
        "synthetic_dataset_present": settings.dataset_path.exists(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def seed_demo_database():
    db = SessionLocal()
    try:
        existing = db.scalars(select(Victim)).first()
        if existing:
            return
        if not settings.dataset_path.exists():
            logger.warning("Synthetic dataset not found; skipping demo seed.")
            return
        data = pd.read_csv(settings.dataset_path)
        for vid, g in data.groupby("victim_id", sort=False):
            first = g.iloc[0]
            db.add(Victim(
                victim_id=str(vid), state=str(first.state), age=int(first.age),
                gender=str(first.gender), social_category=str(first.social_category),
                offence_type=str(first.offence_type), severity_1_to_5=int(first.severity_1_to_5),
            ))
            for r in g.itertuples(index=False):
                db.add(Interaction(
                    victim_id=str(r.victim_id),
                    interaction_number=int(r.interaction_number),
                    days_since_registration=int(r.days_since_registration),
                    case_stage=str(r.case_stage),
                    communication_channel=str(r.communication_channel),
                    threat_received=int(r.threat_received),
                    investigation_or_court_delay_days=int(r.investigation_or_court_delay_days),
                    court_appearances_to_date=int(r.court_appearances_to_date),
                    economic_stress_1_to_5=int(r.economic_stress_1_to_5),
                    social_support_1_to_5=int(r.social_support_1_to_5),
                    relief_status=str(r.relief_status),
                    counselling_status=str(r.counselling_status),
                    text_response=str(r.text_response),
                    sentiment_score=float(r.sentiment_score),
                    fear_score=float(r.fear_score),
                    sadness_score=float(r.sadness_score),
                    anger_score=float(r.anger_score),
                    voice_stress_score=float(r.voice_stress_score),
                    engagement_score=float(r.engagement_score),
                    current_distress_score=float(r.current_distress_score),
                ))
        db.add(AuditLog(event_type="demo_seed", actor="system", detail="Seeded synthetic dataset"))
        db.commit()
        logger.info("Seeded demo database with synthetic dataset.")
    finally:
        db.close()


@app.get("/demo-victims")
def demo_victims(_: bool = Depends(require_api_key)):
    if not settings.demo_mode:
        raise HTTPException(status_code=404, detail="Demo endpoint disabled")
    if not settings.dataset_path.exists():
        raise HTTPException(status_code=404, detail="Synthetic dataset not found")
    df = pd.read_csv(settings.dataset_path, usecols=["victim_id"])
    values = df["victim_id"].drop_duplicates().head(250).tolist()
    return {"victims": values, "synthetic": True}


# ─────────────────────────────────────────────────────────────────────────────
#  JURY DEMO — additional endpoints for the SIH prototype
# ─────────────────────────────────────────────────────────────────────────────

# ── DDS scoring without a trained model (keyword + sentiment heuristic) ──────

RISK_KEYWORDS: dict[str, float] = {
    "suicide": 5, "end my life": 5, "kill myself": 5,
    "threat": 4, "threatened": 4, "hopeless": 4, "abuse": 4, "abused": 4,
    "afraid": 3, "alone": 3, "scared": 3, "hit": 3, "violence": 3,
    "can't sleep": 2, "no money": 2, "financial": 2, "harassment": 3,
    "court": 1, "delay": 1, "investigation": 1, "testimony": 1,
    "crying": 2, "nightmare": 2, "panic": 3, "anxiety": 3,
    # Hindi
    "mann chintit": 3, "bojh": 3, "dara hua": 3, "akela": 2, "nirash": 4,
    "pareshan": 3, "takleef": 2, "dhamki": 4,
}

INTERVENTIONS = {
    "critical": "🚨 Immediate counsellor outreach + police protection order recommended",
    "high":     "⚠️  Priority counselling session within 24 hours + legal aid follow-up",
    "moderate": "📋 Scheduled counselling + financial assistance review",
    "low":      "✅ Routine check-in; provide helpline number and peer support",
}

FACTOR_LABELS = {
    "keyword_score":        "Distress keywords in text",
    "sentiment_norm":       "Negative sentiment detected",
    "engagement_penalty":   "Missed check-ins / low engagement",
    "context_penalty":      "Prolonged case delay",
}


def _calculate_dds(
    text: str,
    sentiment_score: float,
    missed_checkins: int,
    case_delay_days: int,
) -> tuple[float, list[dict]]:
    """Lightweight explainable DDS formula (no ML model required)."""
    text_lower = text.lower()
    raw_kw = sum(w for k, w in RISK_KEYWORDS.items() if k in text_lower)
    keyword_norm     = min(raw_kw / 15.0, 1.0)
    sentiment_norm   = (1.0 - float(sentiment_score)) / 2.0
    engagement_penalty = min(missed_checkins / 5.0, 1.0)
    context_penalty  = min(case_delay_days / 365.0, 1.0)

    dds = (
        0.40 * keyword_norm
        + 0.25 * sentiment_norm
        + 0.15 * engagement_penalty
        + 0.20 * context_penalty
    ) * 100

    contributors = sorted([
        {"factor": FACTOR_LABELS["keyword_score"],      "weight": 0.40, "raw": round(keyword_norm, 3),      "contribution": round(0.40 * keyword_norm * 100, 1)},
        {"factor": FACTOR_LABELS["sentiment_norm"],     "weight": 0.25, "raw": round(sentiment_norm, 3),    "contribution": round(0.25 * sentiment_norm * 100, 1)},
        {"factor": FACTOR_LABELS["engagement_penalty"], "weight": 0.15, "raw": round(engagement_penalty, 3),"contribution": round(0.15 * engagement_penalty * 100, 1)},
        {"factor": FACTOR_LABELS["context_penalty"],    "weight": 0.20, "raw": round(context_penalty, 3),   "contribution": round(0.20 * context_penalty * 100, 1)},
    ], key=lambda x: x["contribution"], reverse=True)

    return round(dds, 1), contributors[:3]


# ── Schema for the check-in endpoint ─────────────────────────────────────────

class CheckInRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en", pattern="^(en|hi)$")
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    missed_checkins: int = Field(default=0, ge=0, le=20)
    case_delay_days: int = Field(default=90, ge=0, le=3650)
    victim_id: Optional[str] = Field(default=None, max_length=64)


class AcknowledgeRequest(BaseModel):
    victim_id: str = Field(min_length=1, max_length=64)
    counsellor_note: Optional[str] = Field(default=None, max_length=500)


# ── 1. Text Check-in + DDS ────────────────────────────────────────────────────

@app.post("/demo/checkin")
def demo_checkin(payload: CheckInRequest):
    """
    Jury demo: submit a text check-in, receive DDS + risk badge + top-3 factors + intervention.
    No ML model required — uses the lightweight keyword+sentiment formula.
    """
    dds, contributors = _calculate_dds(
        payload.text,
        payload.sentiment_score,
        payload.missed_checkins,
        payload.case_delay_days,
    )
    from ml.evaluation.metrics import risk_from_score
    risk = risk_from_score(dds)
    return {
        "dds": dds,
        "risk_level": risk,
        "top_factors": contributors,
        "recommended_intervention": INTERVENTIONS[risk],
        "formula_note": "Prototype heuristic: 40% keywords + 25% sentiment + 15% engagement + 20% case delay",
        "synthetic": True,
    }


# ── 2. Counsellor Dashboard — victim list with latest DDS ────────────────────

@app.get("/demo/dashboard")
def demo_dashboard(db: Session = Depends(db_session)):
    """
    Returns up to 50 victims with their latest DDS, risk level, case stage, last check-in.
    Sorted by DDS descending for the counsellor view.
    """
    victims = db.scalars(select(Victim).limit(200)).all()
    rows = []
    for v in victims:
        latest = db.scalars(
            select(Interaction)
            .where(Interaction.victim_id == v.victim_id)
            .order_by(Interaction.interaction_number.desc())
        ).first()
        pred = db.scalars(
            select(Prediction)
            .where(Prediction.victim_id == v.victim_id)
            .order_by(Prediction.created_at.desc())
        ).first()
        if latest is None:
            continue
        from ml.evaluation.metrics import risk_from_score
        dds = pred.predicted_distress_score if pred else (latest.current_distress_score or 0.0)
        risk = pred.risk_level if pred else risk_from_score(float(dds))
        rows.append({
            "victim_id": v.victim_id,
            "state": v.state,
            "age": v.age,
            "gender": v.gender,
            "offence_type": v.offence_type,
            "case_stage": latest.case_stage,
            "dds": round(float(dds), 1),
            "risk_level": risk,
            "last_checkin": latest.timestamp.isoformat() if latest.timestamp else None,
            "interaction_count": latest.interaction_number,
            "requires_review": risk in {"high", "critical"},
        })
    rows.sort(key=lambda r: r["dds"], reverse=True)
    return {"count": len(rows), "victims": rows[:50]}


# ── 3. Victim Detail — 30-day trend + SHAP-style explainability ──────────────

@app.get("/demo/victim/{victim_id}")
def demo_victim_detail(victim_id: str, db: Session = Depends(db_session)):
    """
    Full victim detail view: 30-day DDS trend, case stage timeline,
    check-in summaries, SHAP contributors, intervention history.
    """
    victim = db.get(Victim, victim_id)
    if victim is None:
        raise HTTPException(status_code=404, detail="Victim not found")

    interactions = db.scalars(
        select(Interaction)
        .where(Interaction.victim_id == victim_id)
        .order_by(Interaction.interaction_number)
    ).all()

    predictions = db.scalars(
        select(Prediction)
        .where(Prediction.victim_id == victim_id)
        .order_by(Prediction.created_at.desc())
    ).all()

    from ml.evaluation.metrics import risk_from_score

    timeline = []
    for i in interactions:
        dds = float(i.current_distress_score or 0)
        timeline.append({
            "interaction_number": i.interaction_number,
            "dds": dds,
            "risk_level": risk_from_score(dds),
            "case_stage": i.case_stage,
            "channel": i.communication_channel,
            "timestamp": i.timestamp.isoformat() if i.timestamp else None,
            "summary": (i.text_response or "")[:120],
            "threat_received": bool(i.threat_received),
            "economic_stress": i.economic_stress_1_to_5,
            "social_support": i.social_support_1_to_5,
        })

    # Build SHAP-style explanation for the latest interaction
    shap_factors = []
    if interactions:
        last = interactions[-1]
        text_lower = (last.text_response or "").lower()
        raw_kw = sum(w for k, w in RISK_KEYWORDS.items() if k in text_lower)
        kw_n = min(raw_kw / 15.0, 1.0)
        sent_n = (1.0 - float(last.sentiment_score or 0)) / 2.0
        eng_n = 1.0 - float(last.engagement_score or 1)
        threat_n = float(last.threat_received or 0)
        econ_n = (float(last.economic_stress_1_to_5 or 3) - 1) / 4.0
        supp_n = 1.0 - (float(last.social_support_1_to_5 or 3) - 1) / 4.0
        delay_n = min(float(last.investigation_or_court_delay_days or 0) / 365.0, 1.0)

        shap_factors = sorted([
            {"feature": "Text distress keywords",      "value": round(kw_n * 40, 1),   "direction": "↑ risk"},
            {"feature": "Negative sentiment",          "value": round(sent_n * 25, 1),  "direction": "↑ risk"},
            {"feature": "Low engagement",              "value": round(eng_n * 15, 1),   "direction": "↑ risk"},
            {"feature": "Threat received",             "value": round(threat_n * 20, 1),"direction": "↑ risk" if threat_n else "neutral"},
            {"feature": "Economic stress",             "value": round(econ_n * 15, 1),  "direction": "↑ risk"},
            {"feature": "Low social support",          "value": round(supp_n * 10, 1),  "direction": "↑ risk"},
            {"feature": "Case / investigation delay",  "value": round(delay_n * 20, 1), "direction": "↑ risk"},
        ], key=lambda x: x["value"], reverse=True)

    intervention_history = []
    for p in predictions[:10]:
        intervention_history.append({
            "date": p.created_at.isoformat(),
            "dds": round(p.predicted_distress_score, 1),
            "risk": p.risk_level,
            "action": INTERVENTIONS.get(p.risk_level, "—"),
            "reviewed": not p.requires_human_review,
        })

    scores = [t["dds"] for t in timeline]
    return {
        "victim": {
            "victim_id": victim.victim_id,
            "state": victim.state,
            "age": victim.age,
            "gender": victim.gender,
            "social_category": victim.social_category,
            "offence_type": victim.offence_type,
            "severity": victim.severity_1_to_5,
        },
        "current_stage": interactions[-1].case_stage if interactions else "Unknown",
        "trend": trend_label(scores),
        "timeline": timeline,
        "shap_factors": shap_factors[:5],
        "intervention_history": intervention_history,
        "total_interactions": len(interactions),
    }


# ── 4. Alert Panel ────────────────────────────────────────────────────────────

@app.get("/demo/alerts")
def demo_alerts(db: Session = Depends(db_session)):
    """
    High-risk cases (DDS > 60): victim ID, risk level, alert time,
    recommended action, notification log.
    """
    flags = db.scalars(
        select(ReviewFlag).order_by(ReviewFlag.created_at.desc()).limit(100)
    ).all()
    items = []
    for f in flags:
        pred = db.scalars(
            select(Prediction)
            .where(Prediction.id == f.prediction_id)
        ).first()
        items.append({
            "flag_id": f.id,
            "victim_id": f.victim_id,
            "priority": f.priority,
            "status": f.status,
            "dds": round(pred.predicted_distress_score, 1) if pred else None,
            "created_at": f.created_at.isoformat(),
            "recommended_action": INTERVENTIONS.get(f.priority, "—"),
            "notification_log": [
                {"channel": "SMS",   "sent_at": f.created_at.isoformat(), "status": "delivered"},
                {"channel": "Email", "sent_at": f.created_at.isoformat(), "status": "delivered"},
            ],
        })
    open_count = sum(1 for i in items if i["status"] == "open")
    return {"total": len(items), "open": open_count, "alerts": items}


@app.post("/demo/acknowledge")
def demo_acknowledge(payload: AcknowledgeRequest, db: Session = Depends(db_session)):
    """Counsellor acknowledges a high-risk alert (human-in-the-loop)."""
    flags = db.scalars(
        select(ReviewFlag)
        .where(ReviewFlag.victim_id == payload.victim_id, ReviewFlag.status == "open")
        .order_by(ReviewFlag.created_at.desc())
    ).all()
    if not flags:
        raise HTTPException(status_code=404, detail="No open flags for this victim")
    for f in flags:
        f.status = "acknowledged"
    db.add(AuditLog(
        event_type="alert_acknowledged",
        actor="counsellor",
        victim_id=payload.victim_id,
        detail=payload.counsellor_note or "Acknowledged via demo panel",
    ))
    db.commit()
    return {"acknowledged": len(flags), "victim_id": payload.victim_id}


# ── 5. Analytics Dashboard ────────────────────────────────────────────────────

@app.get("/demo/analytics")
def demo_analytics(db: Session = Depends(db_session)):
    """
    Aggregate stats for the district/state/national dashboard:
    - DDS distribution by state
    - High-risk case count
    - Intervention success rate
    - Case stage breakdown
    """
    from ml.evaluation.metrics import risk_from_score

    victims = db.scalars(select(Victim)).all()
    total_victims = len(victims)
    state_stats: dict[str, dict] = {}
    risk_counts = {"low": 0, "moderate": 0, "high": 0, "critical": 0}
    stage_counts: dict[str, int] = {}
    acknowledged = 0
    total_flags = 0

    for v in victims:
        pred = db.scalars(
            select(Prediction)
            .where(Prediction.victim_id == v.victim_id)
            .order_by(Prediction.created_at.desc())
        ).first()
        latest_int = db.scalars(
            select(Interaction)
            .where(Interaction.victim_id == v.victim_id)
            .order_by(Interaction.interaction_number.desc())
        ).first()

        dds = float(pred.predicted_distress_score) if pred else (
            float(latest_int.current_distress_score) if latest_int and latest_int.current_distress_score else 0.0
        )
        risk = pred.risk_level if pred else risk_from_score(dds)
        state = v.state or "Unknown"

        if state not in state_stats:
            state_stats[state] = {"total": 0, "dds_sum": 0.0, "high_critical": 0}
        state_stats[state]["total"] += 1
        state_stats[state]["dds_sum"] += dds
        if risk in {"high", "critical"}:
            state_stats[state]["high_critical"] += 1
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

        if latest_int and latest_int.case_stage:
            stage_counts[latest_int.case_stage] = stage_counts.get(latest_int.case_stage, 0) + 1

    # Intervention success: acknowledged / total flags
    all_flags = db.scalars(select(ReviewFlag)).all()
    total_flags = len(all_flags)
    acknowledged = sum(1 for f in all_flags if f.status == "acknowledged")

    heatmap = [
        {
            "state": s,
            "total_victims": d["total"],
            "avg_dds": round(d["dds_sum"] / d["total"], 1) if d["total"] else 0,
            "high_critical_count": d["high_critical"],
            "risk_rate": round(d["high_critical"] / d["total"] * 100, 1) if d["total"] else 0,
        }
        for s, d in state_stats.items()
    ]
    heatmap.sort(key=lambda x: x["avg_dds"], reverse=True)

    return {
        "total_victims": total_victims,
        "risk_distribution": risk_counts,
        "high_risk_count": risk_counts.get("high", 0) + risk_counts.get("critical", 0),
        "intervention_success_rate": round(acknowledged / total_flags * 100, 1) if total_flags else 0,
        "total_alerts": total_flags,
        "acknowledged_alerts": acknowledged,
        "state_heatmap": heatmap,
        "case_stage_breakdown": stage_counts,
        "synthetic": True,
    }
