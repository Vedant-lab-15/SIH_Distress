from __future__ import annotations

from fastapi import Header, HTTPException
from app.backend.config import settings


def require_api_key(x_api_key: str | None = Header(default=None)):
    if not settings.auth_enabled:
        return True
    if not settings.api_key:
        raise HTTPException(status_code=500, detail="AUTH_ENABLED is true but APP_API_KEY is not configured")
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True
