from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from patient_triage.config import Settings
from patient_triage.domain.enums import AgeGroup, Symptom
from patient_triage.domain.patient import Patient


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (0, AgeGroup.PEDIATRIC),
        (17.99, AgeGroup.PEDIATRIC),
        (18, AgeGroup.ADULT),
        (64.99, AgeGroup.ADULT),
        (65, AgeGroup.GERIATRIC),
        (130, AgeGroup.GERIATRIC),
    ],
)
def test_age_group_boundaries(patient_factory, age, expected):
    assert patient_factory(age=age).age_group is expected


@pytest.mark.parametrize("age", [-0.01, 130.01])
def test_invalid_age_rejected(patient_factory, age):
    with pytest.raises(ValidationError):
        patient_factory(age=age)


@pytest.mark.parametrize("patient_id", ["", "has space", "!bad", "x" * 65])
def test_invalid_patient_identifier_rejected(patient_factory, patient_id):
    with pytest.raises(ValidationError):
        patient_factory(patient_id=patient_id)


def test_naive_timestamps_rejected(patient_factory, vitals_factory, now):
    naive = now.replace(tzinfo=None)
    with pytest.raises(ValidationError, match="timezone"):
        patient_factory(vitals=vitals_factory(recorded_at=naive))
    with pytest.raises(ValidationError, match="timezone"):
        patient_factory(arrival_time=naive)


def test_blood_pressure_order_rejected(vitals_factory):
    with pytest.raises(ValidationError, match="diastolic"):
        vitals_factory(systolic_bp_mm_hg=80, diastolic_bp_mm_hg=90)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("heart_rate_bpm", 301),
        ("respiratory_rate_bpm", 101),
        ("systolic_bp_mm_hg", 29),
        ("oxygen_saturation_pct", 101),
        ("temperature_c", 46),
    ],
)
def test_impossible_vital_ranges_rejected(vitals_factory, field, value):
    with pytest.raises(ValidationError):
        vitals_factory(**{field: value})


def test_previous_vitals_must_be_older(patient_factory, vitals_factory, now):
    current = vitals_factory(recorded_at=now - timedelta(minutes=10))
    previous = vitals_factory(recorded_at=now - timedelta(minutes=1))
    with pytest.raises(ValidationError, match="previous vitals"):
        patient_factory(vitals=current, previous_vitals=previous)


def test_review_cannot_precede_arrival(patient_factory, now):
    with pytest.raises(ValidationError, match="before arrival"):
        patient_factory(last_clinical_review_at=now - timedelta(minutes=20))


def test_symptoms_and_tags_are_normalized(patient_factory):
    patient = patient_factory(
        symptoms=[Symptom.COUGH, Symptom.COUGH, Symptom.FEVER],
        scenario_tags=[" Zero History ", "zero_history", ""],
    )
    assert patient.symptoms == [Symptom.COUGH, Symptom.FEVER]
    assert patient.scenario_tags == ["zero_history"]


def test_missing_measurements_are_explicit(vitals_factory):
    vitals = vitals_factory(heart_rate_bpm=None, oxygen_saturation_pct=None)
    assert vitals.missing_measurements() == [
        "heart_rate_bpm",
        "oxygen_saturation_pct",
    ]


def test_extra_fields_are_rejected(patient_factory):
    with pytest.raises(ValidationError):
        patient_factory(real_patient_name="must not be stored")


def test_settings_from_environment(monkeypatch, tmp_path):
    database = tmp_path / "audit.db"
    monkeypatch.setenv("PATIENT_TRIAGE_DATABASE_PATH", str(database))
    monkeypatch.setenv("PATIENT_TRIAGE_BOOTSTRAP_DEMO_DATA", "no")
    monkeypatch.setenv("PATIENT_TRIAGE_NORMAL_CAPACITY", "25")
    monkeypatch.setenv("PATIENT_TRIAGE_SURGE_MULTIPLIER", "4")
    settings = Settings.from_env()
    assert settings.database_path == database
    assert settings.bootstrap_demo_data is False
    assert settings.normal_capacity == 25
    assert settings.surge_multiplier == 4


def test_empty_symptom_list_rejected(patient_factory):
    patient = patient_factory()
    payload = patient.model_dump()
    payload["symptoms"] = []
    with pytest.raises(ValidationError):
        Patient.model_validate(payload)


def test_datetime_type_is_preserved(patient_factory):
    assert isinstance(patient_factory().arrival_time, datetime)
