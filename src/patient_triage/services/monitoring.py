"""Waiting-room monitoring and reassessment decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from patient_triage.domain.enums import AcuityLevel, QueueMode, QueueState
from patient_triage.domain.patient import Patient, require_aware
from patient_triage.models.features import physiology_risk
from patient_triage.rules.thresholds import max_wait_minutes, stale_after_minutes


@dataclass(frozen=True, slots=True)
class MonitoringAssessment:
    state: QueueState
    alerts: tuple[str, ...]
    recommended_action: str


def _is_deteriorating(patient: Patient) -> bool:
    previous = patient.previous_vitals
    current = patient.vitals
    if previous is None:
        return False
    changes = (
        (
            previous.oxygen_saturation_pct is not None
            and current.oxygen_saturation_pct is not None
            and previous.oxygen_saturation_pct - current.oxygen_saturation_pct >= 3
        )
        or (
            previous.systolic_bp_mm_hg is not None
            and current.systolic_bp_mm_hg is not None
            and previous.systolic_bp_mm_hg - current.systolic_bp_mm_hg >= 20
        )
        or (
            previous.heart_rate_bpm is not None
            and current.heart_rate_bpm is not None
            and current.heart_rate_bpm - previous.heart_rate_bpm >= 25
        )
        or (
            previous.respiratory_rate_bpm is not None
            and current.respiratory_rate_bpm is not None
            and current.respiratory_rate_bpm - previous.respiratory_rate_bpm >= 8
        )
    )
    risk_increase = physiology_risk(patient) - physiology_risk(patient, previous) >= 0.2
    return bool(changes or risk_increase)


def assess_monitoring(
    patient: Patient,
    acuity: AcuityLevel,
    now: datetime,
    mode: QueueMode,
) -> MonitoringAssessment:
    now = require_aware(now, "now")
    if patient.arrival_time > now or patient.vitals.recorded_at > now:
        raise ValueError("patient timestamps cannot be in the future")

    alerts: list[str] = []
    vital_age = (now - patient.vitals.recorded_at).total_seconds() / 60
    review_reference = patient.last_clinical_review_at or patient.arrival_time
    review_age = (now - review_reference).total_seconds() / 60
    overdue = review_age >= max_wait_minutes(acuity, mode)
    stale = vital_age > stale_after_minutes(mode)
    deteriorating = _is_deteriorating(patient)

    if acuity is AcuityLevel.CRITICAL:
        alerts.append("critical safety floor: immediate clinical review")
    if deteriorating:
        alerts.append("recorded vital signs indicate deterioration")
    if stale:
        alerts.append("latest vital signs are stale")
    if overdue:
        alerts.append("reassessment threshold has been reached")

    if acuity is AcuityLevel.CRITICAL:
        state = QueueState.CRITICAL_ESCALATION
        action = "Immediate clinician review required"
    elif deteriorating:
        state = QueueState.DETERIORATING
        action = "Reassess immediately and review the changed vital signs"
    elif stale:
        state = QueueState.STALE_INFORMATION
        action = "Repeat vital signs before relying on the recommendation"
    elif overdue:
        state = QueueState.REASSESSMENT_DUE
        action = "Clinical reassessment is due"
    else:
        state = QueueState.STABLE
        action = "Continue monitoring"
    return MonitoringAssessment(state, tuple(alerts), action)
