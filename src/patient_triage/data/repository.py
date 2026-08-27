"""Thread-safe in-memory patient repository for the prototype."""

from __future__ import annotations

from threading import RLock

from patient_triage.domain.enums import PatientStatus
from patient_triage.domain.errors import DuplicatePatientError, PatientNotFoundError
from patient_triage.domain.patient import Patient, VitalSigns


class InMemoryPatientRepository:
    def __init__(self) -> None:
        self._patients: dict[str, Patient] = {}
        self._lock = RLock()

    def add(self, patient: Patient) -> Patient:
        with self._lock:
            if patient.patient_id in self._patients:
                raise DuplicatePatientError(
                    f"patient '{patient.patient_id}' already exists"
                )
            self._patients[patient.patient_id] = patient.model_copy(deep=True)
            return patient.model_copy(deep=True)

    def get(self, patient_id: str) -> Patient:
        with self._lock:
            try:
                return self._patients[patient_id].model_copy(deep=True)
            except KeyError as exc:
                raise PatientNotFoundError(
                    f"patient '{patient_id}' was not found"
                ) from exc

    def list_all(self) -> list[Patient]:
        with self._lock:
            return [
                patient.model_copy(deep=True) for patient in self._patients.values()
            ]

    def list_waiting(self) -> list[Patient]:
        return [
            patient
            for patient in self.list_all()
            if patient.status is PatientStatus.WAITING
        ]

    def update_vitals(self, patient_id: str, vitals: VitalSigns) -> Patient:
        with self._lock:
            patient = self.get(patient_id)
            payload = patient.model_dump()
            payload.update(
                {
                    "previous_vitals": patient.vitals.model_dump(),
                    "vitals": vitals.model_dump(),
                    "last_clinical_review_at": vitals.recorded_at,
                }
            )
            updated = Patient.model_validate(payload)
            self._patients[patient_id] = updated
            return updated.model_copy(deep=True)

    def set_status(self, patient_id: str, status: PatientStatus) -> Patient:
        with self._lock:
            patient = self.get(patient_id)
            payload = patient.model_dump()
            payload["status"] = status
            updated = Patient.model_validate(payload)
            self._patients[patient_id] = updated
            return updated.model_copy(deep=True)

    def replace_all(self, patients: list[Patient]) -> None:
        ids = [patient.patient_id for patient in patients]
        if len(ids) != len(set(ids)):
            raise DuplicatePatientError(
                "scenario contains duplicate patient identifiers"
            )
        with self._lock:
            self._patients = {
                patient.patient_id: patient.model_copy(deep=True)
                for patient in patients
            }

    def clear(self) -> None:
        with self._lock:
            self._patients.clear()
