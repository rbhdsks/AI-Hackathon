"""Visible confidence estimates based on data quality and model state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from patient_triage.domain.enums import ConfidenceLevel, QueueMode, Symptom
from patient_triage.domain.patient import Patient, require_aware
from patient_triage.rules.thresholds import stale_after_minutes


@dataclass(frozen=True, slots=True)
class ConfidenceAssessment:
    score: float
    level: ConfidenceLevel
    reasons: tuple[str, ...]


def assess_confidence(
    patient: Patient,
    now: datetime,
    mode: QueueMode,
    model_available: bool = True,
) -> ConfidenceAssessment:
    now = require_aware(now, "now")
    if patient.vitals.recorded_at > now:
        raise ValueError("vital-sign timestamp cannot be in the future")

    score = 1.0
    reasons: list[str] = []
    missing = patient.vitals.missing_measurements()
    if missing:
        score -= min(len(missing) * 0.08, 0.4)
        reasons.append(f"{len(missing)} vital-sign measurements are missing")
    if not patient.has_prior_record:
        score -= 0.12
        reasons.append("no prior record is available")
    if Symptom.UNKNOWN in patient.symptoms:
        score -= 0.18
        reasons.append("the presentation is marked ambiguous")
    if patient.pain_score is None:
        score -= 0.05
        reasons.append("pain score is missing")

    vital_age = (now - patient.vitals.recorded_at).total_seconds() / 60
    if vital_age > stale_after_minutes(mode):
        score -= 0.25
        reasons.append("the latest vital signs are stale")
    if not model_available:
        score = min(score, 0.35)
        reasons.append("the CDM is unavailable; rule-only fallback is active")

    score = max(min(score, 1.0), 0.0)
    if score >= 0.8:
        level = ConfidenceLevel.HIGH
    elif score >= 0.55:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW
    return ConfidenceAssessment(score, level, tuple(reasons))
