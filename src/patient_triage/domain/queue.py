"""Queue recommendation models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from patient_triage.domain.enums import (
    AcuityLevel,
    ConfidenceLevel,
    QueueMode,
    QueueState,
)
from patient_triage.domain.patient import PatientId


class QueueEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: int = Field(ge=1)
    patient_id: PatientId
    acuity: AcuityLevel
    acuity_label: str
    safety_floor: AcuityLevel
    cdm_probability: float | None = Field(default=None, ge=0, le=1)
    cdm_utility: float | None = None
    base_utility: float | None = None
    context_effect: float | None = None
    confidence: ConfidenceLevel
    confidence_score: float = Field(ge=0, le=1)
    wait_minutes: float = Field(ge=0)
    state: QueueState
    reasons: list[str] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    triggered_rules: list[str] = Field(default_factory=list)
    recommended_action: str
    is_stale: bool = False
    is_overridden: bool = False
    override_reason: str | None = None


class QueueSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    mode: QueueMode
    model_status: str
    model_version: str
    patient_count: int = Field(ge=0)
    queue_pressure: float = Field(ge=0)
    entries: list[QueueEntry]
    warnings: list[str] = Field(default_factory=list)


class OverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: PatientId
    target_position: int = Field(ge=1)
    clinician_id: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    reason: str = Field(min_length=10, max_length=500)
