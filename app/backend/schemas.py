from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class InteractionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    victim_id: str = Field(min_length=1, max_length=64)
    interaction_number: int = Field(ge=1, le=100)
    days_since_registration: int = Field(ge=0, le=5000)
    state: str = Field(min_length=1, max_length=64)
    age: int = Field(ge=18, le=120)
    gender: str = Field(min_length=1, max_length=32)
    social_category: str = Field(min_length=1, max_length=32)
    offence_type: str = Field(min_length=1, max_length=64)
    severity_1_to_5: int = Field(ge=1, le=5)
    case_stage: str = Field(min_length=1, max_length=64)
    communication_channel: str = Field(min_length=1, max_length=64)
    threat_received: int = Field(ge=0, le=1)
    investigation_or_court_delay_days: int = Field(ge=0, le=5000)
    court_appearances_to_date: int = Field(ge=0, le=200)
    economic_stress_1_to_5: int = Field(ge=1, le=5)
    social_support_1_to_5: int = Field(ge=1, le=5)
    relief_status: str = Field(min_length=1, max_length=64)
    counselling_status: str = Field(min_length=1, max_length=64)
    text_response: str = Field(default="", max_length=4000)
    sentiment_score: float = Field(ge=-1, le=1)
    fear_score: float = Field(ge=0, le=1)
    sadness_score: float = Field(ge=0, le=1)
    anger_score: float = Field(ge=0, le=1)
    voice_stress_score: float = Field(ge=0, le=1)
    engagement_score: float = Field(ge=0, le=1)
    current_distress_score: float = Field(ge=0, le=100)


class PredictionResponse(BaseModel):
    predicted_distress_score: float
    risk_level: str
    requires_human_review: bool
    model_version: str
    trend: str | None = None
    contributors: list[dict[str, Any]] = []


class BatchRequest(BaseModel):
    interactions: list[InteractionInput] = Field(min_length=1, max_length=1000)
