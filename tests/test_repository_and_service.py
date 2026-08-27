from __future__ import annotations

from datetime import timedelta

import pytest

from patient_triage.config import Settings
from patient_triage.data.generator import generate_normal_scenario
from patient_triage.data.repository import InMemoryPatientRepository
from patient_triage.domain.enums import PatientStatus
from patient_triage.domain.errors import (
    DuplicatePatientError,
    InvalidTimelineError,
    PatientNotFoundError,
)
from patient_triage.services.triage import TriageService
from patient_triage.storage.sqlite_audit import SQLiteAuditStore


def test_repository_add_get_returns_copies(patient_factory):
    repository = InMemoryPatientRepository()
    patient = repository.add(patient_factory())
    patient.scenario_tags.append("mutated")
    assert repository.get(patient.patient_id).scenario_tags == []


def test_repository_duplicate_and_not_found(patient_factory):
    repository = InMemoryPatientRepository()
    repository.add(patient_factory())
    with pytest.raises(DuplicatePatientError):
        repository.add(patient_factory())
    with pytest.raises(PatientNotFoundError):
        repository.get("SYN-MISSING")


def test_repository_update_vitals(patient_factory, vitals_factory, now):
    repository = InMemoryPatientRepository()
    original = repository.add(patient_factory())
    new_vitals = vitals_factory(recorded_at=now, heart_rate_bpm=120)
    updated = repository.update_vitals(original.patient_id, new_vitals)
    assert updated.previous_vitals == original.vitals
    assert updated.vitals.heart_rate_bpm == 120
    assert updated.last_clinical_review_at == now


def test_status_filters_waiting_patients(patient_factory):
    repository = InMemoryPatientRepository()
    repository.add(patient_factory("SYN-A"))
    repository.add(patient_factory("SYN-B"))
    repository.set_status("SYN-A", PatientStatus.IN_TREATMENT)
    assert [p.patient_id for p in repository.list_waiting()] == ["SYN-B"]


def test_replace_all_and_clear(patient_factory):
    repository = InMemoryPatientRepository()
    repository.replace_all([patient_factory("SYN-A"), patient_factory("SYN-B")])
    assert len(repository.list_all()) == 2
    with pytest.raises(DuplicatePatientError):
        repository.replace_all([patient_factory("SYN-A"), patient_factory("SYN-A")])
    repository.clear()
    assert repository.list_all() == []


@pytest.fixture
def triage_service(tmp_path):
    settings = Settings(database_path=tmp_path / "audit.db", bootstrap_demo_data=False)
    store = SQLiteAuditStore(settings.database_path)
    service = TriageService(
        settings=settings,
        repository=InMemoryPatientRepository(),
        audit_store=store,
    )
    yield service
    store.close()


def test_service_intake_and_audit(triage_service, patient_factory, now):
    triage_service.intake(patient_factory(), actor_id="tester", now=now)
    events = triage_service.audit_store.list_events()
    assert events[0].event_type == "patient_intake"
    assert triage_service.audit_store.verify_chain()


def test_service_rejects_far_future_intake(triage_service, patient_factory, now):
    patient = patient_factory(arrival_time=now + timedelta(minutes=6))
    with pytest.raises(InvalidTimelineError, match="arrival"):
        triage_service.intake(patient, now=now)


def test_service_rejects_future_vitals(
    triage_service, patient_factory, vitals_factory, now
):
    patient = patient_factory(
        vitals=vitals_factory(recorded_at=now + timedelta(minutes=6))
    )
    with pytest.raises(InvalidTimelineError, match="vital"):
        triage_service.intake(patient, now=now)


def test_service_rejects_older_vital_update(
    triage_service, patient_factory, vitals_factory, now
):
    patient = patient_factory()
    triage_service.intake(patient, now=now)
    older = vitals_factory(
        recorded_at=patient.vitals.recorded_at - timedelta(minutes=1)
    )
    with pytest.raises(InvalidTimelineError, match="older"):
        triage_service.update_vitals(patient.patient_id, older, now=now)


def test_service_updates_status_and_queue(triage_service, patient_factory, now):
    triage_service.intake(patient_factory(), now=now)
    triage_service.set_status("SYN-TEST", PatientStatus.DISCHARGED)
    assert triage_service.rank_queue(now=now).patient_count == 0


def test_load_scenario_replaces_queue_and_clears_state(triage_service, now):
    patients = generate_normal_scenario(now)
    triage_service.load_scenario(patients, scenario_name="normal")
    snapshot = triage_service.rank_queue(now=now)
    assert snapshot.patient_count == 20
    assert triage_service.audit_store.list_events()[0].event_type == "queue_ranked"
