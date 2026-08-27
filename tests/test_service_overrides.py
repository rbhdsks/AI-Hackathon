from __future__ import annotations

from datetime import datetime

import pytest

from patient_triage.config import Settings
from patient_triage.data.generator import generate_normal_scenario
from patient_triage.data.repository import InMemoryPatientRepository
from patient_triage.domain.queue import OverrideRequest
from patient_triage.services.triage import TriageService
from patient_triage.storage.sqlite_audit import SQLiteAuditStore


def test_service_override_persists_and_is_audited(tmp_path, now):
    settings = Settings(database_path=tmp_path / "audit.db", bootstrap_demo_data=False)
    store = SQLiteAuditStore(settings.database_path)
    service = TriageService(
        settings=settings,
        repository=InMemoryPatientRepository(),
        audit_store=store,
    )
    try:
        service.load_scenario(generate_normal_scenario(now), scenario_name="normal")
        service.rank_queue(now=now)
        request = OverrideRequest(
            patient_id="SYN-011",
            target_position=5,
            clinician_id="nurse_01",
            reason="Direct reassessment is needed because the presentation is ambiguous",
        )
        overridden = service.override_queue(request, now=now)
        assert (
            next(e for e in overridden.entries if e.patient_id == "SYN-011").position
            == 5
        )
        recomputed = service.rank_queue(now=now)
        assert (
            next(e for e in recomputed.entries if e.patient_id == "SYN-011").position
            == 5
        )
        event = next(
            e for e in store.list_events() if e.event_type == "clinician_override"
        )
        assert event.actor_id == "nurse_01"
        assert event.payload["target_position"] == 5
    finally:
        store.close()


def test_service_override_rejects_naive_clock(tmp_path, now):
    settings = Settings(database_path=tmp_path / "audit.db", bootstrap_demo_data=False)
    store = SQLiteAuditStore(settings.database_path)
    service = TriageService(
        settings=settings,
        repository=InMemoryPatientRepository(),
        audit_store=store,
    )
    try:
        service.load_scenario(generate_normal_scenario(now), scenario_name="normal")
        service.rank_queue(now=now)
        request = OverrideRequest(
            patient_id="SYN-011",
            target_position=5,
            clinician_id="nurse_01",
            reason="Direct reassessment is needed because the presentation is ambiguous",
        )
        with pytest.raises(ValueError, match="must include a timezone"):
            service.override_queue(request, now=datetime(2026, 8, 25, 12, 0))
    finally:
        store.close()
