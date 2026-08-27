"""Metrics that avoid unsupported clinical-outcome claims."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from patient_triage.domain.enums import AcuityLevel
from patient_triage.domain.patient import Patient
from patient_triage.domain.queue import QueueSnapshot


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_count: int = Field(ge=0)
    labelled_patient_count: int = Field(ge=0)
    critical_missed: int = Field(ge=0)
    under_triage_count: int = Field(ge=0)
    over_triage_count: int = Field(ge=0)
    high_risk_detection_rate: float | None = Field(default=None, ge=0, le=1)
    low_confidence_count: int = Field(ge=0)
    reassessment_alert_count: int = Field(ge=0)
    explanation_coverage: float = Field(ge=0, le=1)
    mean_wait_minutes: float = Field(ge=0)
    model_status: str


def evaluate_snapshot(
    snapshot: QueueSnapshot, patients: list[Patient]
) -> EvaluationReport:
    expected_by_id = {
        patient.patient_id: patient.expected_acuity
        for patient in patients
        if patient.expected_acuity is not None
    }
    labelled_entries = [
        entry for entry in snapshot.entries if entry.patient_id in expected_by_id
    ]
    under = 0
    over = 0
    critical_missed = 0
    high_risk_total = 0
    high_risk_detected = 0
    for entry in labelled_entries:
        expected = expected_by_id[entry.patient_id]
        assert expected is not None
        if int(entry.acuity) > int(expected):
            under += 1
        elif int(entry.acuity) < int(expected):
            over += 1
        if (
            expected is AcuityLevel.CRITICAL
            and entry.acuity is not AcuityLevel.CRITICAL
        ):
            critical_missed += 1
        if int(expected) <= int(AcuityLevel.EMERGENT):
            high_risk_total += 1
            if int(entry.acuity) <= int(AcuityLevel.EMERGENT):
                high_risk_detected += 1

    count = len(snapshot.entries)
    low_confidence = sum(entry.confidence.value == "low" for entry in snapshot.entries)
    reassessment_alerts = sum(
        any("reassessment" in alert.lower() for alert in entry.alerts)
        for entry in snapshot.entries
    )
    explanation_coverage = (
        sum(bool(entry.reasons) for entry in snapshot.entries) / count if count else 1.0
    )
    mean_wait = (
        sum(entry.wait_minutes for entry in snapshot.entries) / count if count else 0.0
    )
    detection_rate = high_risk_detected / high_risk_total if high_risk_total else None
    return EvaluationReport(
        patient_count=count,
        labelled_patient_count=len(labelled_entries),
        critical_missed=critical_missed,
        under_triage_count=under,
        over_triage_count=over,
        high_risk_detection_rate=detection_rate,
        low_confidence_count=low_confidence,
        reassessment_alert_count=reassessment_alerts,
        explanation_coverage=round(explanation_coverage, 4),
        mean_wait_minutes=round(mean_wait, 2),
        model_status=snapshot.model_status,
    )
