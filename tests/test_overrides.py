from __future__ import annotations

import pytest
from pydantic import ValidationError

from patient_triage.domain.enums import (
    AcuityLevel,
    ConfidenceLevel,
    QueueMode,
    QueueState,
)
from patient_triage.domain.errors import InvalidOverrideError
from patient_triage.domain.queue import OverrideRequest, QueueEntry, QueueSnapshot
from patient_triage.services.overrides import apply_override


def _entry(position: int, patient_id: str, acuity: AcuityLevel) -> QueueEntry:
    return QueueEntry(
        position=position,
        patient_id=patient_id,
        acuity=acuity,
        acuity_label=acuity.label,
        safety_floor=acuity,
        confidence=ConfidenceLevel.HIGH,
        confidence_score=1,
        wait_minutes=5,
        state=QueueState.STABLE,
        recommended_action="Continue monitoring",
    )


def _snapshot(now) -> QueueSnapshot:
    return QueueSnapshot(
        generated_at=now,
        mode=QueueMode.NORMAL,
        model_status="ready",
        model_version="test",
        patient_count=3,
        queue_pressure=0.15,
        entries=[
            _entry(1, "SYN-A", AcuityLevel.CRITICAL),
            _entry(2, "SYN-B", AcuityLevel.URGENT),
            _entry(3, "SYN-C", AcuityLevel.LESS_URGENT),
        ],
    )


def test_valid_override_repositions_and_marks_entry(now):
    request = OverrideRequest(
        patient_id="SYN-C",
        target_position=1,
        clinician_id="nurse_01",
        reason="Direct clinical observation indicates higher current concern",
    )
    updated = apply_override(_snapshot(now), request)
    assert [entry.patient_id for entry in updated.entries] == [
        "SYN-C",
        "SYN-A",
        "SYN-B",
    ]
    assert updated.entries[0].is_overridden
    assert updated.entries[0].override_reason == request.reason


def test_unknown_override_patient_rejected(now):
    request = OverrideRequest(
        patient_id="SYN-X",
        target_position=1,
        clinician_id="nurse_01",
        reason="A sufficiently detailed reason for this synthetic override",
    )
    with pytest.raises(InvalidOverrideError, match="not in"):
        apply_override(_snapshot(now), request)


def test_out_of_range_override_rejected(now):
    request = OverrideRequest(
        patient_id="SYN-B",
        target_position=4,
        clinician_id="nurse_01",
        reason="A sufficiently detailed reason for this synthetic override",
    )
    with pytest.raises(InvalidOverrideError, match="outside"):
        apply_override(_snapshot(now), request)


def test_critical_downward_move_adds_safety_warning(now):
    request = OverrideRequest(
        patient_id="SYN-A",
        target_position=3,
        clinician_id="nurse_01",
        reason="Clinician accepts responsibility after direct reassessment",
    )
    updated = apply_override(_snapshot(now), request)
    assert any("safety conflict" in warning.lower() for warning in updated.warnings)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "patient_id": "SYN-A",
            "target_position": 0,
            "clinician_id": "nurse",
            "reason": "long enough reason",
        },
        {
            "patient_id": "SYN-A",
            "target_position": 1,
            "clinician_id": "!",
            "reason": "long enough reason",
        },
        {
            "patient_id": "SYN-A",
            "target_position": 1,
            "clinician_id": "nurse",
            "reason": "short",
        },
    ],
)
def test_override_request_validation(payload):
    with pytest.raises(ValidationError):
        OverrideRequest(**payload)
