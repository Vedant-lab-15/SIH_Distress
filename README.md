# AI-Powered Dynamic Mental Health Monitoring System

> **SurakshaMind** — Consent-based, multilingual AI distress monitoring for victims of atrocities.

**Problem Statement ID:** 26094 &nbsp;|&nbsp; **Ministry:** MoSJE (Ministry of Social Justice & Empowerment) &nbsp;|&nbsp; **Edition:** SIH 2026

🔗 **Live Demo:** `[DEPLOY URL HERE]` &nbsp;|&nbsp; 📄 **Docs:** `/docs` &nbsp;|&nbsp; 🐙 **GitHub:** `[REPO URL HERE]`

> ⚠️ All data is synthetic. This prototype does not diagnose mental illness or make autonomous high-impact decisions.

---

## What it does

- **Monitors** victim well-being continuously via chatbot, IVRS, SMS, mobile app and web portal — in English, Hindi and 8 regional languages
- **Scores** each check-in using a Dynamic Distress Score (DDS, 0–100) built from text, voice biomarkers, engagement patterns and case-context signals
- **Detects** deviation from each victim's personal baseline using longitudinal XGBoost + SHAP, flagging escalation *before* crisis
- **Alerts** counsellors and district authorities with explainable, human-review-required notifications for High/Critical cases
- **Intervenes** with recommended actions (counselling, legal aid, protection orders, financial assistance) and tracks outcomes for reassessment

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite (demo) / PostgreSQL (prod) |
| AI / ML | XGBoost (Dynamic), SHAP / LIME, Scikit-learn, Librosa (voice), PyTorch, MuRIL / IndicBERT |
| Frontend | Vanilla JS SPA (demo), React.js (production dashboard), Flutter (mobile) |
| Security | OAuth 2.0, AES-256 encryption, DPDP Act 2023 compliance, Pydantic validation, audit logs |
| Deployment | Docker, docker-compose, Azure Container Apps |

---

## The 6 Screens

| Screen | What it shows |
|---|---|
| **Home** | Problem statement, system flow diagram, live KPIs, feature overview, channel support |
| **Check-in** | Text & Voice (IVRS-simulated) check-in → DDS gauge + top-3 factors + intervention |
| **Counsellor Dashboard** | All victims sorted by DDS with search, filter, risk badges, click-to-detail |
| **Victim Detail** | 30-day DDS trend chart, case-stage progress, SHAP explainability, intervention history |
| **Alert Panel** | High/Critical flags with channel source, notification log, human acknowledgment |
| **Analytics** | State heatmap, risk distribution (doughnut), case-stage bar chart, success rate |

---

## How to run locally

```bash
# 1. Clone and enter
git clone [REPO URL HERE]
cd ai_dynamic_distress_monitoring_26094

# 2. Create virtual environment
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Retrain the model — pre-trained artifact included
python scripts/train_model.py

# 5. Start the server
uvicorn app.backend.main:app --host 0.0.0.0 --port 8000

# 6. Open in browser
# http://localhost:8000          → SurakshaMind prototype
# http://localhost:8000/docs     → Interactive API docs
```

> Demo mode seeds 2,000 synthetic victims from `data/synthetic/synthetic_distress_dataset.csv` automatically on first startup. No extra steps needed.

### Render.com (cloud deployment)

```bash
# Render injects the $PORT environment variable automatically.
# The render.yaml in the repo root configures this automatically.
uvicorn app.backend.main:app --host 0.0.0.0 --port $PORT
```

Deploy steps:
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service → connect your repo
3. Render auto-detects `render.yaml` → click **Create**
4. Live URL appears in ~3 minutes at `https://sanjeevani-sih.onrender.com`

### Docker

```bash
docker compose up --build
# App available at http://localhost:8000
```

### Run tests

```bash
pytest -q
# Expected: 10 passed
```

---

## Project Structure

```
ai_dynamic_distress_monitoring_26094/
├── app/
│   ├── backend/          # FastAPI app, database models, schemas, security
│   └── frontend/         # index.html, app.js, styles.css
├── ml/
│   ├── data/             # Dataset loader
│   ├── features/         # Dynamic longitudinal feature engineering
│   ├── inference/        # Predictor class
│   ├── preprocessing/    # ColumnTransformer pipeline
│   ├── training/         # Train script, victim-level split
│   ├── evaluation/       # Regression + classification metrics, fairness
│   └── explainability/   # SHAP utilities
├── data/
│   ├── raw/              # Source Excel workbook
│   ├── processed/        # Engineered features CSV
│   └── synthetic/        # 20,000-row synthetic benchmark
├── models/               # Trained .joblib artifacts
├── reports/              # metrics.json, SHAP figures, fairness CSV
├── scripts/              # prepare_data, generate_synthetic_data, train_model
├── tests/                # 10 pytest tests
├── docs/                 # Architecture, API reference, demo script, references
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

---

## Model Performance (Synthetic Benchmark)

| Model | Test MAE | Test R² | High+Critical Recall |
|---|---:|---:|---:|
| Mean Baseline | 20.79 | -0.004 | 0.000 |
| Current Distress Only | 8.10 | 0.834 | 0.767 |
| Ridge | 4.76 | **0.944** | 0.846 |
| **Dynamic XGBoost** ✓ | **4.82** | 0.943 | **0.866** |

> Deployed model: Dynamic XGBoost — highest high/critical recall + SHAP tree explainer support.
> All metrics are from the synthetic benchmark and do not constitute clinical validation.

---

## Roadmap

Post-submission features planned for v2:

- [ ] Voice biomarker module — MFCC2 + Loudness (validated cross-linguistic PTSD markers, Kathan et al. Interspeech 2024)
- [ ] Multilingual NLP — MuRIL / IndicBERT fine-tuned on Hindi + 8 regional languages
- [ ] LSTM distress forecaster — Prophet-LSTM hybrid for 7-day escalation prediction
- [ ] IVRS / SMS integration — Twilio + BHIM/NPCI gateway for rural reach
- [ ] DPDP consent manager — granular, revocable consent per DPDP Act 2023 §6
- [ ] Full documentation PDF — model card, data governance, audit trail
- [ ] PostgreSQL + Azure managed identity — production-grade persistence
- [ ] Formal fairness & safety review — independent ethics board evaluation

---

## Limitations

This is a prototype built on a synthetic benchmark. Metrics are not evidence of clinical validity. The system must not be used for clinical, legal, welfare, police or rehabilitation decisions without:
- validated clinical questionnaires and professional governance
- formal ethical review and privacy compliance audit
- qualified human oversight at every decision point

---

## License

MIT — see `LICENSE`

## Contact

Team: `[TEAM NAME HERE]`  
Institution: `[INSTITUTION HERE]`  
Email: `[EMAIL HERE]`
