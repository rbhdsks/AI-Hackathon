"""Minimum-necessary readiness tasks for pharmacy and blood-bank views."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock

from patient_triage.domain.enums import (
    AcuityLevel,
    CoordinationDomain,
    Symptom,
    TaskStatus,
)
from patient_triage.domain.errors import CoordinationTaskNotFoundError
from patient_triage.domain.operations import CoordinationTask
from patient_triage.domain.patient import Patient, require_aware
from patient_triage.domain.queue import QueueSnapshot


class CoordinationService:
    def __init__(self) -> None:
        self._acknowledgements: dict[str, tuple[str, datetime]] = {}
        self._lock = RLock()

    def reset(self) -> None:
        with self._lock:
            self._acknowledgements.clear()

    def list_tasks(
        self,
        domain: CoordinationDomain,
        patients: list[Patient],
        snapshot: QueueSnapshot,
    ) -> list[CoordinationTask]:
        entry_by_id = {entry.patient_id: entry for entry in snapshot.entries}
        patient_by_id = {patient.patient_id: patient for patient in patients}
        tasks: list[CoordinationTask] = []
        for patient_id, entry in entry_by_id.items():
            patient = patient_by_id[patient_id]
            task = self._derive_task(domain, patient, entry.acuity)
            if task is not None:
                tasks.append(task)
        return sorted(tasks, key=lambda item: (item.priority, item.patient_id))

    def acknowledge(
        self,
        *,
        domain: CoordinationDomain,
        task_id: str,
        actor_id: str,
        patients: list[Patient],
        snapshot: QueueSnapshot,
        now: datetime | None = None,
    ) -> CoordinationTask:
        observed_at = require_aware(now or datetime.now(UTC), "now")
        tasks = self.list_tasks(domain, patients, snapshot)
        task = next((item for item in tasks if item.task_id == task_id), None)
        if task is None:
            raise CoordinationTaskNotFoundError(
                f"coordination task '{task_id}' was not found"
            )
        with self._lock:
            self._acknowledgements[task_id] = (actor_id, observed_at)
        return task.model_copy(
            update={
                "status": TaskStatus.ACKNOWLEDGED,
                "acknowledged_by": actor_id,
                "acknowledged_at": observed_at,
            }
        )

    def _derive_task(
        self,
        domain: CoordinationDomain,
        patient: Patient,
        acuity: AcuityLevel,
    ) -> CoordinationTask | None:
        summary: str | None = None
        reason: str | None = None
        if domain is CoordinationDomain.PHARMACY:
            if int(acuity) <= int(AcuityLevel.EMERGENT):
                summary = "Prepare for urgent medication review"
                reason = f"Current triage acuity is {acuity.label}."
            elif patient.pain_score is not None and patient.pain_score >= 7:
                summary = "Review analgesia readiness"
                reason = f"Recorded pain score is {patient.pain_score}/10."
            elif not patient.has_prior_record:
                summary = "Medication-history reconciliation needed"
                reason = "No prior record is available in the synthetic intake."
        else:
            severe_bleeding = Symptom.SEVERE_BLEEDING in patient.symptoms
            shock_signal = (
                patient.vitals.systolic_bp_mm_hg is not None
                and patient.vitals.systolic_bp_mm_hg < 90
            )
            critical_trauma = (
                Symptom.TRAUMA in patient.symptoms and acuity is AcuityLevel.CRITICAL
            )
            if severe_bleeding or shock_signal or critical_trauma:
                summary = "Review transfusion-readiness signal"
                signals = [
                    label
                    for active, label in (
                        (severe_bleeding, "severe bleeding symptom"),
                        (shock_signal, "low systolic pressure"),
                        (critical_trauma, "critical trauma"),
                    )
                    if active
                ]
                reason = "Signals: " + ", ".join(signals) + "."
        if summary is None or reason is None:
            return None
        task_id = f"{domain.value}:{patient.patient_id}"
        with self._lock:
            acknowledgement = self._acknowledgements.get(task_id)
        return CoordinationTask(
            task_id=task_id,
            domain=domain,
            patient_id=patient.patient_id,
            priority=int(acuity),
            summary=summary,
            reason=reason,
            status=(
                TaskStatus.ACKNOWLEDGED
                if acknowledgement is not None
                else TaskStatus.PENDING
            ),
            acknowledged_by=acknowledgement[0] if acknowledgement else None,
            acknowledged_at=acknowledgement[1] if acknowledgement else None,
        )
