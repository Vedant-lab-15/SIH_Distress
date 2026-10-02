# Deployment Guide

## Local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/prepare_data.py
python scripts/train_model.py
uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Docker

On a Docker-capable host:

```bash
docker compose up --build
```

This starts the FastAPI API and dashboard on port 8000.

## Production database

Set:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
```

The PostgreSQL driver is included in `requirements.txt`. Run the service with
production credentials supplied through the platform secret manager.

## Production model storage

Set:

```text
MODEL_DIR=/app/models
```

For multi-instance deployments, store immutable model artifacts in controlled object storage or a model registry and mount/load by a versioned artifact path.

## Authentication

Set:

```text
AUTH_ENABLED=true
APP_API_KEY=<secret>
```

This enables a simple API-key guard suitable for a demo/integration boundary. For real deployment, use institutional SSO/OIDC and role-based authorization.

## Network security

Terminate TLS at a reverse proxy or managed load balancer. Restrict database network access to the application tier. Do not expose the database directly to public networks.

## Real-data gate

Do not turn on real-data collection merely by changing an environment variable. A real deployment requires institutional governance, validated data pipelines, access control, consent/lawful-basis decisions, retention rules, clinical/professional review, security assessment, and formal legal/compliance review.
