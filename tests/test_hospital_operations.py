from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from patient_triage.config import Settings
from patient_triage.data.generator import generate_scenario
from patient_triage.data.repository import InMemoryPatientRepository
from patient_triage.domain.enums import (
    CoordinationDomain,
    Permission,
    StaffRole,
    TaskStatus,
)
from patient_triage.domain.errors import (
    CoordinationTaskNotFoundError,
    PermissionDeniedError,
)
from patient_triage.domain.hospital import (
    HospitalProfile,
    load_access_control,
    load_hospital_profile,
)
from patient_triage.domain.operations import BedSlot, CoordinationTask
from patient_triage.services.access_control import AccessController
from patient_triage.services.bed_board import build_bed_board
from patient_triage.services.coordination import CoordinationService
from patient_triage.services.ranking import RankingService
from patient_triage.services.triage import TriageService
from patient_triage.storage.sqlite_audit import SQLiteAuditStore


def test_hospital_profile_and_access_matrix() -> None:
    profile = load_hospital_profile(Path("configs/district_hospital.json"))
    matrix = load_access_control(Path("configs/rbac.json"))
    assert profile.ed_beds == 18
    assert profile.shift.duration_hours == 12
    assert profile.staffing.clinical_staff == 21
    assert sum(zone.bed_count for zone in profile.zones) == 18

    access = AccessController(matrix)
    access.require(StaffRole.NURSE, Permission.VITALS_WRITE)
    with pytest.raises(PermissionDeniedError):
        access.require(StaffRole.PHARMACY, Permission.PATIENT_READ)
    with pytest.raises(ValueError, match="no access policy"):
        matrix.model_copy(update={"roles": []}).policy_for(StaffRole.DOCTOR)


def test_hospital_profile_rejects_inconsistent_capacity() -> None:
    payload = load_hospital_profile(Path("configs/district_hospital.json")).model_dump(
        mode="json"
    )
    payload["ed_beds"] = 19
    with pytest.raises(ValidationError, match="zone bed counts"):
        HospitalProfile.model_validate(payload)
    payload["ed_beds"] = 300
    with pytest.raises(ValidationError, match="ED beds cannot exceed"):
        HospitalProfile.model_validate(payload)


def test_bed_slot_and_coordination_models_validate(now) -> None:
    with pytest.raises(ValidationError, match="empty bed"):
        BedSlot(
            bed_id="ED-01",
            zone="Acute care",
            status="empty",
            patient_id="SYN-001",
        )
    with pytest.raises(ValidationError, match="requires an actor"):
        CoordinationTask(
            task_id="pharmacy:SYN-001",
            domain="pharmacy",
            patient_id="SYN-001",
            priority=1,
            summary="Urgent review",
            reason="Synthetic critical case.",
            status="acknowledged",
            acknowledged_at=now,
        )


def test_bed_board_normal_surge_and_empty(now) -> None:
    profile = load_hospital_profile(Path("configs/district_hospital.json"))
    ranker = RankingService()
    normal = ranker.rank(generate_scenario("normal", now), now=now)
    normal_board = build_bed_board(normal, profile)
    assert (normal_board.occupied_beds, normal_board.waiting_for_bed) == (18, 2)
    assert len(normal_board.beds) == 18
    assert {bed.zone for bed in normal_board.beds} == {
        "Resuscitation",
        "Acute care",
        "Observation",
    }

    surge = ranker.rank(generate_scenario("surge", now), now=now)
    surge_board = build_bed_board(surge, profile)
    assert (surge_board.occupied_beds, surge_board.waiting_for_bed) == (18, 42)

    empty = ranker.rank([], now=now)
    empty_board = build_bed_board(empty, profile)
    assert empty_board.empty_beds == 18
    assert all(bed.status.value == "empty" for bed in empty_board.beds)


def test_coordination_acknowledgement_reset_and_missing(now) -> None:
    patients = generate_scenario("normal", now)
    snapshot = RankingService().rank(patients, now=now)
    coordination = CoordinationService()
    pharmacy = coordination.list_tasks(CoordinationDomain.PHARMACY, patients, snapshot)
    blood = coordination.list_tasks(CoordinationDomain.BLOOD_BANK, patients, snapshot)
    assert pharmacy
    assert any(item.patient_id == "SYN-004" for item in blood)

    selected = pharmacy[0]
    acknowledged = coordination.acknowledge(
        domain=CoordinationDomain.PHARMACY,
        task_id=selected.task_id,
        actor_id="pharmacist_01",
        patients=patients,
        snapshot=snapshot,
        now=now,
    )
    assert acknowledged.status is TaskStatus.ACKNOWLEDGED
    refreshed = coordination.list_tasks(CoordinationDomain.PHARMACY, patients, snapshot)
    assert (
        next(item for item in refreshed if item.task_id == selected.task_id).status
        is TaskStatus.ACKNOWLEDGED
    )
    coordination.reset()
    reset = coordination.list_tasks(CoordinationDomain.PHARMACY, patients, snapshot)
    assert (
        next(item for item in reset if item.task_id == selected.task_id).status
        is TaskStatus.PENDING
    )
    with pytest.raises(CoordinationTaskNotFoundError):
        coordination.acknowledge(
            domain=CoordinationDomain.PHARMACY,
            task_id="pharmacy:missing",
            actor_id="pharmacist_01",
            patients=patients,
            snapshot=snapshot,
            now=now,
        )


def test_triage_service_operational_methods(tmp_path) -> None:
    now = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
    store = SQLiteAuditStore(tmp_path / "ops.db")
    service = TriageService(
        settings=Settings(database_path=tmp_path / "ops.db"),
        repository=InMemoryPatientRepository(),
        audit_store=store,
    )
    try:
        service.load_scenario(generate_scenario("normal", now), scenario_name="normal")
        assert service.bed_board(now=now).total_beds == 18
        assert len(service.baseline_report(now=now).results) == 6
        tasks = service.coordination_tasks(CoordinationDomain.PHARMACY, now=now)
        acknowledged = service.acknowledge_coordination_task(
            CoordinationDomain.PHARMACY,
            tasks[0].task_id,
            "pharmacist_01",
            now=now,
        )
        assert acknowledged.status is TaskStatus.ACKNOWLEDGED
        assert any(
            event.event_type == "pharmacy_task_acknowledged"
            for event in store.list_events(100)
        )
    finally:
        store.close()
