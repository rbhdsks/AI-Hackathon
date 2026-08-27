from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from patient_triage.api.app import create_app
from patient_triage.config import Settings


@pytest.fixture
def client(tmp_path):
    app = create_app(
        Settings(database_path=tmp_path / "api.db", bootstrap_demo_data=True)
    )
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_openapi(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["prototype_only"] is True
    assert client.get("/openapi.json").status_code == 200


def test_bootstrap_patients_and_queue(client):
    patients = client.get("/v1/patients")
    queue = client.get("/v1/queue")
    assert patients.status_code == 200
    assert len(patients.json()) == 20
    assert queue.status_code == 200
    assert queue.json()["patient_count"] == 20
    assert queue.json()["model_status"] == "ready"


def test_duplicate_intake_returns_conflict(client):
    patient = client.get("/v1/patients").json()[0]
    response = client.post("/v1/patients", json=patient)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_invalid_patient_returns_validation_error(client):
    response = client.post(
        "/v1/patients",
        json={"patient_id": "bad id", "age_years": -1},
    )
    assert response.status_code == 422


def test_update_vitals_and_missing_patient(client):
    patient = client.get("/v1/patients").json()[8]
    vitals = patient["vitals"]
    vitals["heart_rate_bpm"] = 140
    vitals["recorded_at"] = datetime.now(UTC).isoformat()
    updated = client.put(
        f"/v1/patients/{patient['patient_id']}/vitals",
        params={"actor_id": "nurse_01"},
        json=vitals,
    )
    assert updated.status_code == 200
    assert updated.json()["vitals"]["heart_rate_bpm"] == 140
    missing = client.put("/v1/patients/SYN-MISSING/vitals", json=vitals)
    assert missing.status_code == 404


def test_status_removes_patient_from_waiting_queue(client):
    before = client.get("/v1/queue").json()["patient_count"]
    response = client.patch(
        "/v1/patients/SYN-020/status",
        params={"patient_status": "discharged"},
    )
    assert response.status_code == 200
    assert client.get("/v1/queue").json()["patient_count"] == before - 1


def test_normal_and_surge_scenarios(client):
    headers = {"X-Demo-Role": "administration"}
    surge = client.post("/v1/simulations/surge", headers=headers)
    assert surge.status_code == 200
    assert surge.json()["patient_count"] == 60
    queue = client.get("/v1/queue").json()
    assert queue["mode"] == "surge"
    assert queue["queue_pressure"] == 3
    normal = client.post("/v1/simulations/normal", headers=headers)
    assert normal.json()["patient_count"] == 20


def test_role_permissions_and_operational_endpoints(client):
    nurse = {"X-Demo-Role": "nurse"}
    doctor = {"X-Demo-Role": "doctor"}
    pharmacy = {"X-Demo-Role": "pharmacy"}
    administration = {"X-Demo-Role": "administration"}
    blood_bank = {"X-Demo-Role": "blood_bank"}

    access = client.get("/v1/access")
    assert access.status_code == 200
    assert {item["role"] for item in access.json()["roles"]} == {
        "nurse",
        "doctor",
        "pharmacy",
        "administration",
        "blood_bank",
    }
    assert client.get("/v1/infrastructure", headers=pharmacy).status_code == 200

    beds = client.get("/v1/beds", headers=nurse)
    assert beds.status_code == 200
    assert beds.json()["total_beds"] == 18
    assert beds.json()["occupied_beds"] == 18
    assert beds.json()["waiting_for_bed"] == 2

    assert client.get("/v1/audit", headers=nurse).status_code == 403
    assert client.get("/v1/queue", headers=pharmacy).status_code == 403
    assert client.get("/v1/patients", headers=administration).status_code == 403
    assert client.post("/v1/simulations/surge", headers=doctor).status_code == 403

    benchmark = client.get("/v1/evaluation/baselines", headers=administration)
    assert benchmark.status_code == 200
    assert len(benchmark.json()["results"]) == 6

    pharmacy_tasks = client.get("/v1/coordination/pharmacy", headers=pharmacy)
    assert pharmacy_tasks.status_code == 200
    task = pharmacy_tasks.json()[0]
    acknowledged = client.post(
        f"/v1/coordination/pharmacy/{task['task_id']}/acknowledge",
        headers=pharmacy,
        json={"actor_id": "pharmacist_01"},
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"
    assert (
        client.get("/v1/coordination/pharmacy", headers=blood_bank).status_code == 403
    )

    blood_tasks = client.get("/v1/coordination/blood_bank", headers=blood_bank)
    assert blood_tasks.status_code == 200
    assert any(item["patient_id"] == "SYN-004" for item in blood_tasks.json())


def test_role_header_validation_and_missing_coordination_task(client):
    assert (
        client.get("/v1/infrastructure", headers={"X-Demo-Role": "unknown"}).status_code
        == 422
    )
    missing = client.post(
        "/v1/coordination/pharmacy/pharmacy:missing/acknowledge",
        headers={"X-Demo-Role": "pharmacy"},
        json={"actor_id": "pharmacist_01"},
    )
    assert missing.status_code == 404


def test_deterioration_endpoint(client):
    before = next(
        item
        for item in client.get("/v1/patients").json()
        if item["patient_id"] == "SYN-015"
    )
    response = client.post("/v1/simulations/deteriorate/SYN-015")
    assert response.status_code == 200
    assert (
        response.json()["vitals"]["heart_rate_bpm"] > before["vitals"]["heart_rate_bpm"]
    )
    queue_entry = next(
        item
        for item in client.get("/v1/queue").json()["entries"]
        if item["patient_id"] == "SYN-015"
    )
    assert queue_entry["state"] in {"deteriorating", "critical_escalation"}


def test_model_failure_endpoint_behavior(client):
    response = client.get("/v1/queue", params={"simulate_model_failure": "true"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_status"] == "fallback"
    assert all(item["is_stale"] for item in payload["entries"])


def test_override_and_audit(client):
    client.get("/v1/queue")
    response = client.post(
        "/v1/queue/overrides",
        json={
            "patient_id": "SYN-011",
            "target_position": 5,
            "clinician_id": "nurse_01",
            "reason": "Ambiguous presentation needs earlier direct reassessment",
        },
    )
    assert response.status_code == 200
    selected = next(
        item for item in response.json()["entries"] if item["patient_id"] == "SYN-011"
    )
    assert selected["position"] == 5
    assert selected["is_overridden"] is True
    events = client.get("/v1/audit", params={"limit": 100})
    assert events.status_code == 200
    assert any(event["event_type"] == "clinician_override" for event in events.json())
    assert client.get("/v1/audit/verify").json() == {"valid": True}


def test_invalid_override_and_audit_limit(client):
    short_reason = client.post(
        "/v1/queue/overrides",
        json={
            "patient_id": "SYN-011",
            "target_position": 1,
            "clinician_id": "nurse_01",
            "reason": "short",
        },
    )
    assert short_reason.status_code == 422
    outside = client.post(
        "/v1/queue/overrides",
        json={
            "patient_id": "SYN-011",
            "target_position": 100,
            "clinician_id": "nurse_01",
            "reason": "A valid but out-of-range synthetic override reason",
        },
    )
    assert outside.status_code == 400
    assert client.get("/v1/audit", params={"limit": 0}).status_code == 422


def test_empty_application_accepts_new_patient(tmp_path, now, patient_factory):
    app = create_app(
        Settings(database_path=tmp_path / "empty.db", bootstrap_demo_data=False)
    )
    with TestClient(app) as empty_client:
        assert empty_client.get("/v1/queue").json()["patient_count"] == 0
        response = empty_client.post(
            "/v1/patients", json=patient_factory().model_dump(mode="json")
        )
        assert response.status_code == 201
        assert empty_client.get("/v1/queue").json()["patient_count"] == 1
