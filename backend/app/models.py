"""ORM tables. Types are portable between SQLite and PostgreSQL (JSON, String, DateTime).

Privacy: no table stores names, email addresses, IP addresses, credentials, or message
bodies. Participants are identified only by random pseudonymous codes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    mode: Mapped[str] = mapped_column(String(16), index=True)  # demo | study | api
    kind: Mapped[str] = mapped_column(String(16))  # simulated | external
    policy: Mapped[str] = mapped_column(String(64), index=True)
    policy_spec: Mapped[dict[str, Any]] = mapped_column(JSON)
    scenario_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    seed: Mapped[int] = mapped_column(Integer, default=0)
    episode: Mapped[int] = mapped_column(Integer, default=0)
    participant_code: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    condition: Mapped[str | None] = mapped_column(String(64), nullable=True)
    block: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explanation_mode: Mapped[str] = mapped_column(String(16), default="full")
    status: Mapped[str] = mapped_column(String(24), default="running", index=True)
    step_index: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[dict[str, Any]] = mapped_column(JSON)
    outcome: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class EventRow(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    type: Mapped[str] = mapped_column(String(32), index=True)
    mode: Mapped[str] = mapped_column(String(16), index=True)
    scenario_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    policy: Mapped[str] = mapped_column(String(64), index=True)
    participant_code: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    condition: Mapped[str | None] = mapped_column(String(64), nullable=True)
    step_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str | None] = mapped_column(String(128), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    intervention: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[str | None] = mapped_column(String(8), index=True, nullable=True)
    user_response: Mapped[str | None] = mapped_column(String(16), nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class InterventionRow(Base):
    __tablename__ = "interventions"
    __table_args__ = (UniqueConstraint("session_id", "intervention_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intervention_id: Mapped[str] = mapped_column(String(128), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    step_index: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision: Mapped[dict[str, Any]] = mapped_column(JSON)
    response: Mapped[str | None] = mapped_column(String(16), nullable=True)
    answers: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    response_time_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    why_requests: Mapped[int] = mapped_column(Integer, default=0)


class ExperimentRow(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    progress_done: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExperimentEpisodeRow(Base):
    __tablename__ = "experiment_episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    policy: Mapped[str] = mapped_column(String(64), index=True)
    condition: Mapped[str] = mapped_column(String(64), index=True)
    episode: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class ExperimentRecordRow(Base):
    __tablename__ = "experiment_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    policy: Mapped[str] = mapped_column(String(64), index=True)
    condition: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(16))
    intervention: Mapped[bool] = mapped_column(Boolean)
    risk_level: Mapped[str] = mapped_column(String(8), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class ParticipantRow(Base):
    __tablename__ = "participants"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    number: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    explanation_mode: Mapped[str] = mapped_column(String(16))
    plan: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    consented: Mapped[bool] = mapped_column(Boolean, default=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


class QuestionnaireResponseRow(Base):
    __tablename__ = "questionnaire_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    participant_code: Mapped[str] = mapped_column(ForeignKey("participants.code", ondelete="CASCADE"), index=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    block: Mapped[int | None] = mapped_column(Integer, nullable=True)
    policy: Mapped[str | None] = mapped_column(String(64), nullable=True)
    instrument_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    responses: Mapped[dict[str, Any]] = mapped_column(JSON)
    score: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class StudyConfigRow(Base):
    __tablename__ = "study_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
