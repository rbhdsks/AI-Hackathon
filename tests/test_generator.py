from __future__ import annotations

import json
from pathlib import Path

import pytest

from patient_triage.data.generator import (
    deteriorated_vitals,
    generate_normal_scenario,
    generate_scenario,
    generate_surge_scenario,
)
from patient_triage.domain.patient import Patient


def test_normal_scenario_has_required_cases(now):
    patients = generate_normal_scenario(now)
    tags = {tag for patient in patients for tag in patient.scenario_tags}
    assert len(patients) == 20
    assert len({patient.patient_id for patient in patients}) == 20
    assert {
        "pediatric",
        "geriatric",
        "ambiguous",
        "zero_history",
        "deteriorating",
        "unsafe_wait",
    } <= tags


def test_surge_scenario_is_deterministic(now):
    first = generate_surge_scenario(now)
    second = generate_surge_scenario(now)
    assert len(first) == 60
    assert [patient.model_dump() for patient in first] == [
        patient.model_dump() for patient in second
    ]


@pytest.mark.parametrize(
    ("filename", "expected_count"),
    [("patients_normal.json", 20), ("patients_surge.json", 60)],
)
def test_packaged_synthetic_fixtures_validate(filename, expected_count):
    path = Path("data/synthetic") / filename
    payload = json.loads(path.read_text(encoding="utf-8"))

    patients = [Patient.model_validate(item) for item in payload["patients"]]

    assert len(patients) == expected_count
    assert len({patient.patient_id for patient in patients}) == expected_count
    assert "not for clinical use" in payload["prototype_warning"]


def test_generate_scenario_router(now):
    assert len(generate_scenario(" normal ", now)) == 20
    assert len(generate_scenario("SURGE", now)) == 60
    with pytest.raises(ValueError, match="normal"):
        generate_scenario("unknown", now)


def test_deteriorated_vitals_are_newer_and_worse(patient_factory, now):
    patient = patient_factory()
    updated = deteriorated_vitals(patient, now)
    assert updated.recorded_at == now
    assert updated.heart_rate_bpm > patient.vitals.heart_rate_bpm
    assert updated.oxygen_saturation_pct < patient.vitals.oxygen_saturation_pct
