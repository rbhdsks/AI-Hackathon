from __future__ import annotations

from datetime import timedelta

import pytest

from patient_triage.domain.enums import (
    AcuityLevel,
    ConfidenceLevel,
    QueueMode,
    QueueState,
    Symptom,
)
from patient_triage.models.confidence import assess_confidence
from patient_triage.services.monitoring import assess_monitoring


def test_complete_current_record_has_high_confidence(patient_factory, now):
    result = assess_confidence(patient_factory(), now, QueueMode.NORMAL)
    assert result.level is ConfidenceLevel.HIGH
    assert result.score == 1


def test_missing_ambiguous_zero_history_is_low_confidence(
    patient_factory, vitals_factory, now
):
    patient = patient_factory(
        symptoms=[Symptom.UNKNOWN],
        prior_record=False,
        pain=None,
        vitals=vitals_factory(
            heart_rate_bpm=None,
            respiratory_rate_bpm=None,
            systolic_bp_mm_hg=None,
            oxygen_saturation_pct=None,
        ),
    )
    result = assess_confidence(patient, now, QueueMode.NORMAL)
    assert result.level is ConfidenceLevel.LOW
    assert len(result.reasons) >= 3


def test_stale_threshold_is_shorter_in_surge(patient_factory, vitals_factory, now):
    patient = patient_factory(
        vitals=vitals_factory(recorded_at=now - timedelta(minutes=20))
    )
    normal = assess_confidence(patient, now, QueueMode.NORMAL)
    surge = assess_confidence(patient, now, QueueMode.SURGE)
    assert normal.score > surge.score


def test_model_failure_caps_confidence(patient_factory, now):
    result = assess_confidence(
        patient_factory(), now, QueueMode.NORMAL, model_available=False
    )
    assert result.level is ConfidenceLevel.LOW
    assert result.score <= 0.35


def test_future_vitals_rejected_by_confidence(patient_factory, vitals_factory, now):
    patient = patient_factory(
        vitals=vitals_factory(recorded_at=now + timedelta(seconds=1))
    )
    with pytest.raises(ValueError, match="future"):
        assess_confidence(patient, now, QueueMode.NORMAL)


def test_stable_monitoring_state(patient_factory, now):
    result = assess_monitoring(
        patient_factory(arrival_minutes=5), AcuityLevel.URGENT, now, QueueMode.NORMAL
    )
    assert result.state is QueueState.STABLE


def test_critical_state_has_precedence(patient_factory, now):
    result = assess_monitoring(
        patient_factory(arrival_minutes=100),
        AcuityLevel.CRITICAL,
        now,
        QueueMode.NORMAL,
    )
    assert result.state is QueueState.CRITICAL_ESCALATION
    assert "Immediate" in result.recommended_action


def test_deterioration_detected(patient_factory, vitals_factory, now):
    previous = vitals_factory(
        recorded_at=now - timedelta(minutes=15),
        oxygen_saturation_pct=98,
        heart_rate_bpm=80,
    )
    current = vitals_factory(
        recorded_at=now - timedelta(minutes=1),
        oxygen_saturation_pct=94,
        heart_rate_bpm=110,
    )
    patient = patient_factory(vitals=current, previous_vitals=previous)
    result = assess_monitoring(patient, AcuityLevel.URGENT, now, QueueMode.NORMAL)
    assert result.state is QueueState.DETERIORATING


def test_stale_vitals_detected(patient_factory, vitals_factory, now):
    patient = patient_factory(
        arrival_minutes=10,
        vitals=vitals_factory(recorded_at=now - timedelta(minutes=31)),
    )
    result = assess_monitoring(patient, AcuityLevel.NON_URGENT, now, QueueMode.NORMAL)
    assert result.state is QueueState.STALE_INFORMATION


def test_overdue_reassessment_detected(patient_factory, now):
    patient = patient_factory(arrival_minutes=31)
    result = assess_monitoring(patient, AcuityLevel.URGENT, now, QueueMode.NORMAL)
    assert result.state is QueueState.REASSESSMENT_DUE


def test_surge_reassessment_threshold(patient_factory, now):
    patient = patient_factory(arrival_minutes=16)
    normal = assess_monitoring(patient, AcuityLevel.URGENT, now, QueueMode.NORMAL)
    surge = assess_monitoring(patient, AcuityLevel.URGENT, now, QueueMode.SURGE)
    assert normal.state is QueueState.STABLE
    assert surge.state is QueueState.REASSESSMENT_DUE


def test_future_monitoring_timestamp_rejected(patient_factory, now):
    patient = patient_factory(arrival_time=now + timedelta(seconds=1))
    with pytest.raises(ValueError, match="future"):
        assess_monitoring(patient, AcuityLevel.URGENT, now, QueueMode.NORMAL)
