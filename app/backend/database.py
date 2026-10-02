from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import (
    Boolean, DateTime, Float, Integer, String, Text, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.backend.config import settings

if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "", 1)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Victim(Base):
    __tablename__ = "victims"
    victim_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    social_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    offence_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity_1_to_5: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Interaction(Base):
    __tablename__ = "interactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    victim_id: Mapped[str] = mapped_column(String(64), index=True)
    interaction_number: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    days_since_registration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    case_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    communication_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    threat_received: Mapped[int | None] = mapped_column(Integer, nullable=True)
    investigation_or_court_delay_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    court_appearances_to_date: Mapped[int | None] = mapped_column(Integer, nullable=True)
    economic_stress_1_to_5: Mapped[int | None] = mapped_column(Integer, nullable=True)
    social_support_1_to_5: Mapped[int | None] = mapped_column(Integer, nullable=True)
    relief_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    counselling_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    text_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fear_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sadness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    anger_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    voice_stress_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    engagement_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_distress_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    victim_id: Mapped[str] = mapped_column(String(64), index=True)
    interaction_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    predicted_distress_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(32))
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    model_version: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class ReviewFlag(Base):
    __tablename__ = "review_flags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    victim_id: Mapped[str] = mapped_column(String(64), index=True)
    prediction_id: Mapped[int] = mapped_column(Integer)
    priority: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(128), default="system")
    victim_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(bind=engine)
