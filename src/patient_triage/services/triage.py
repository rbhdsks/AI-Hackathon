"""High-level use cases for intake, ranking, monitoring, and overrides."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from threading import RLock

from patient_triage.config import Settings
from patient_triage.data.repository import InMemoryPatientRepository
from patient_triage.domain.enums import CoordinationDomain, PatientStatus, QueueMode
from patient_triage.domain.errors import InvalidTimelineError
from patient_triage.domain.hospital import (
    AccessControlMatrix,
    HospitalProfile,
    load_access_control,
    load_hospital_profile,
)
from patient_triage.domain.operations import BedBoard, CoordinationTask
from patient_triage.domain.patient import Patient, VitalSigns, require_aware
from patient_triage.domain.queue import OverrideRequest, QueueSnapshot
from patient_triage.evaluation.baselines import (
    BaselineBenchmarkReport,
    compare_baselines,
)
from patient_triage.services.access_control import AccessController
from patient_triage.services.bed_board import build_bed_board
from patient_triage.services.coordination import CoordinationService
from patient_triage.services.overrides import apply_override
from patient_triage.services.ranking import RankingService
from patient_triage.storage.sqlite_audit import SQLiteAuditStore


class TriageService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: InMemoryPatientRepository,
        audit_store: SQLiteAuditStore,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.audit_store = audit_store
        self.hospital_profile: HospitalProfile = load_hospital_profile(
            settings.hospital_profile_path
        )
        self.access_matrix: AccessControlMatrix = load_access_control(
            settings.rbac_path
        )
        self.access = AccessController(self.access_matrix)
        self.coordination = CoordinationService()
        self.ranking = RankingService(
            normal_capacity=settings.normal_capacity,
            surge_multiplier=settings.surge_multiplier,
            model_version=settings.model_version,
        )
        self._overrides: list[OverrideRequest] = []
        self._latest_snapshot: QueueSnapshot | None = None
        self._lock = RLock()

    def _validate_clock(self, patient: Patient, now: datetime) -> None:
        tolerance = timedelta(minutes=self.settings.allowed_clock_skew_minutes)
        if patient.arrival_time > now + tolerance:
            raise InvalidTimelineError("arrival time is too far in the future")
        if patient.vitals.recorded_at > now + tolerance:
            raise InvalidTimelineError("vital-sign timestamp is too far in the future")

    def intake(
        self,
        patient: Patient,
        *,
        actor_id: str = "demo-intake",
        now: datetime | None = None,
    ) -> Patient:
        observed_at = now or datetime.now(UTC)
        observed_at = require_aware(observed_at, "now")
        self._validate_clock(patient, observed_at)
        stored = self.repository.add(patient)
        self.audit_store.append(
            actor_id=actor_id,
            event_type="patient_intake",
            patient_id=patient.patient_id,
            payload={
                "age_group": patient.age_group.value,
                "symptoms": [item.value for item in patient.symptoms],
                "has_prior_record": patient.has_prior_record,
            },
            model_version=self.settings.model_version,
            occurred_at=observed_at,
        )
        return stored

    def list_patients(self) -> list[Patient]:
        return self.repository.list_all()

    def bed_board(
        self,
        *,
        now: datetime | None = None,
        simulate_model_failure: bool = False,
    ) -> BedBoard:
        snapshot = self.rank_queue(
            now=now,
            simulate_model_failure=simulate_model_failure,
            audit=False,
        )
        return build_bed_board(snapshot, self.hospital_profile)

    def baseline_report(
        self,
        *,
        now: datetime | None = None,
    ) -> BaselineBenchmarkReport:
        snapshot = self.rank_queue(now=now, audit=False)
        return compare_baselines(
            self.repository.list_waiting(),
            snapshot,
            self.hospital_profile,
        )

    def coordination_tasks(
        self,
        domain: CoordinationDomain,
        *,
        now: datetime | None = None,
    ) -> list[CoordinationTask]:
        snapshot = self.rank_queue(now=now, audit=False)
        return self.coordination.list_tasks(
            domain,
            self.repository.list_waiting(),
            snapshot,
        )

    def acknowledge_coordination_task(
        self,
        domain: CoordinationDomain,
        task_id: str,
        actor_id: str,
        *,
        now: datetime | None = None,
    ) -> CoordinationTask:
        observed_at = require_aware(now or datetime.now(UTC), "now")
        snapshot = self.rank_queue(now=observed_at, audit=False)
        task = self.coordination.acknowledge(
            domain=domain,
            task_id=task_id,
            actor_id=actor_id,
            patients=self.repository.list_waiting(),
            snapshot=snapshot,
            now=observed_at,
        )
        self.audit_store.append(
            actor_id=actor_id,
            event_type=f"{domain.value}_task_acknowledged",
            patient_id=task.patient_id,
            payload={"task_id": task.task_id, "summary": task.summary},
            model_version=self.settings.model_version,
            occurred_at=observed_at,
        )
        return task

    def update_vitals(
        self,
        patient_id: str,
        vitals: VitalSigns,
        *,
        actor_id: str = "demo-clinician",
        now: datetime | None = None,
    ) -> Patient:
        observed_at = now or datetime.now(UTC)
        observed_at = require_aware(observed_at, "now")
        tolerance = timedelta(minutes=self.settings.allowed_clock_skew_minutes)
        if vitals.recorded_at > observed_at + tolerance:
            raise InvalidTimelineError("vital-sign timestamp is too far in the future")
        patient = self.repository.get(patient_id)
        if vitals.recorded_at < patient.vitals.recorded_at:
            raise InvalidTimelineError(
                "new vital signs cannot be older than current vital signs"
            )
        updated = self.repository.update_vitals(patient_id, vitals)
        self.audit_store.append(
            actor_id=actor_id,
            event_type="vitals_updated",
            patient_id=patient_id,
            payload={"recorded_at": vitals.recorded_at.isoformat()},
            model_version=self.settings.model_version,
            occurred_at=observed_at,
        )
        return updated

    def set_status(
        self,
        patient_id: str,
        status: PatientStatus,
        *,
        actor_id: str = "demo-clinician",
    ) -> Patient:
        updated = self.repository.set_status(patient_id, status)
        self.audit_store.append(
            actor_id=actor_id,
            event_type="patient_status_changed",
            patient_id=patient_id,
            payload={"status": status.value},
            model_version=self.settings.model_version,
        )
        return updated

    def rank_queue(
        self,
        *,
        now: datetime | None = None,
        mode: QueueMode | None = None,
        simulate_model_failure: bool = False,
        audit: bool = True,
    ) -> QueueSnapshot:
        observed_at = now or datetime.now(UTC)
        observed_at = require_aware(observed_at, "now")
        snapshot = self.ranking.rank(
            self.repository.list_waiting(),
            now=observed_at,
            mode=mode,
            simulate_model_failure=simulate_model_failure,
        )
        with self._lock:
            active_ids = {entry.patient_id for entry in snapshot.entries}
            self._overrides = [
                item for item in self._overrides if item.patient_id in active_ids
            ]
            for override in self._overrides:
                if override.target_position <= len(snapshot.entries):
                    snapshot = apply_override(snapshot, override)
            self._latest_snapshot = snapshot.model_copy(deep=True)
        if audit:
            self.audit_store.append(
                actor_id="system",
                event_type="queue_ranked",
                payload={
                    "patient_count": snapshot.patient_count,
                    "mode": snapshot.mode.value,
                    "model_status": snapshot.model_status,
                },
                model_version=self.settings.model_version,
                occurred_at=observed_at,
            )
        return snapshot

    def override_queue(
        self,
        request: OverrideRequest,
        *,
        now: datetime | None = None,
    ) -> QueueSnapshot:
        observed_at = now or datetime.now(UTC)
        observed_at = require_aware(observed_at, "now")
        with self._lock:
            base = self._latest_snapshot or self.rank_queue(
                now=observed_at, audit=False
            )
            updated = apply_override(base, request)
            self._overrides = [
                item
                for item in self._overrides
                if item.patient_id != request.patient_id
            ]
            self._overrides.append(request)
            self._latest_snapshot = updated.model_copy(deep=True)
        selected = next(
            entry for entry in updated.entries if entry.patient_id == request.patient_id
        )
        self.audit_store.append(
            actor_id=request.clinician_id,
            event_type="clinician_override",
            patient_id=request.patient_id,
            payload={
                "target_position": request.target_position,
                "reason": request.reason.strip(),
                "acuity": int(selected.acuity),
                "safety_conflict": any(
                    "safety conflict" in warning.lower() for warning in updated.warnings
                ),
            },
            model_version=self.settings.model_version,
            occurred_at=observed_at,
        )
        return updated

    def load_scenario(
        self,
        patients: list[Patient],
        *,
        scenario_name: str,
        actor_id: str = "demo-controller",
    ) -> None:
        self.repository.replace_all(patients)
        with self._lock:
            self._overrides.clear()
            self._latest_snapshot = None
        self.coordination.reset()
        self.audit_store.append(
            actor_id=actor_id,
            event_type="scenario_loaded",
            payload={"scenario": scenario_name, "patient_count": len(patients)},
            model_version=self.settings.model_version,
        )
