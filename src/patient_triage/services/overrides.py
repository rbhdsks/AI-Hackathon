"""Clinician-controlled queue override logic."""

from __future__ import annotations

from patient_triage.domain.enums import AcuityLevel
from patient_triage.domain.errors import InvalidOverrideError
from patient_triage.domain.queue import OverrideRequest, QueueSnapshot


def apply_override(snapshot: QueueSnapshot, request: OverrideRequest) -> QueueSnapshot:
    if request.target_position > len(snapshot.entries):
        raise InvalidOverrideError("target position is outside the current queue")
    matching = [
        entry for entry in snapshot.entries if entry.patient_id == request.patient_id
    ]
    if not matching:
        raise InvalidOverrideError("override patient is not in the current queue")

    entries = [entry.model_copy(deep=True) for entry in snapshot.entries]
    current_index = next(
        index
        for index, entry in enumerate(entries)
        if entry.patient_id == request.patient_id
    )
    selected = entries.pop(current_index)
    entries.insert(request.target_position - 1, selected)
    for position, entry in enumerate(entries, start=1):
        entry.position = position
        if entry.patient_id == request.patient_id:
            entry.is_overridden = True
            entry.override_reason = request.reason.strip()

    warnings = list(snapshot.warnings)
    if (
        selected.acuity is AcuityLevel.CRITICAL
        and request.target_position > current_index + 1
    ):
        warnings.append(
            "Clinician override moved a critical patient downward; safety conflict is logged"
        )
    return snapshot.model_copy(update={"entries": entries, "warnings": warnings})
