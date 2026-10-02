from __future__ import annotations

from pydantic import BaseModel
from pathlib import Path
import os


class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "demo")
    demo_mode: bool = os.getenv("DEMO_MODE", "true").lower() == "true"
    # SQLite path: defaults to ./runtime/demo.sqlite locally.
    # On Render (or any read-only filesystem), set DATABASE_URL=sqlite:////tmp/demo.sqlite
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./runtime/demo.sqlite")
    model_dir: Path = Path(os.getenv("MODEL_DIR", "./models"))
    dataset_path: Path = Path(os.getenv(
        "DATASET_PATH", "./data/synthetic/synthetic_distress_dataset.csv"
    ))
    model_version: str = os.getenv("MODEL_VERSION", "dynamic-xgb-v1.0")
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    api_key: str | None = os.getenv("APP_API_KEY")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    # Default to wildcard so Render / cloud deployments work out of the box.
    # Set ALLOWED_ORIGINS=https://yourdomain.com in production to restrict.
    allowed_origins: list[str] = [x.strip() for x in os.getenv(
        "ALLOWED_ORIGINS", "*"
    ).split(",") if x.strip()]
    emergency_contact_placeholder: str = os.getenv(
        "EMERGENCY_CONTACT_PLACEHOLDER",
        "[CONFIGURE OFFICIAL EMERGENCY / HELPLINE CONTACT]"
    )


settings = Settings()
