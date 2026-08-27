from __future__ import annotations

import pytest

from patient_triage.domain.enums import AcuityLevel, Consciousness, Symptom
from patient_triage.rules.safety_rules import evaluate_safety


@pytest.mark.parametrize(
    ("rule_id", "symptoms", "vital_updates", "age", "distress", "expected"),
    [
        (
            "SAFE-001",
            [Symptom.COUGH],
            {"oxygen_saturation_pct": 89},
            35,
            False,
            AcuityLevel.CRITICAL,
        ),
        (
            "SAFE-002",
            [Symptom.DIZZINESS],
            {"systolic_bp_mm_hg": 89, "diastolic_bp_mm_hg": 55},
            35,
            False,
            AcuityLevel.CRITICAL,
        ),
        (
            "SAFE-003",
            [Symptom.TRAUMA],
            {"consciousness": Consciousness.UNRESPONSIVE},
            35,
            True,
            AcuityLevel.CRITICAL,
        ),
        (
            "SAFE-004",
            [Symptom.HEADACHE],
            {"consciousness": Consciousness.RESPONDS_TO_PAIN},
            35,
            False,
            AcuityLevel.EMERGENT,
        ),
        ("SAFE-005", [Symptom.SEVERE_BLEEDING], {}, 35, True, AcuityLevel.CRITICAL),
        ("SAFE-006", [Symptom.SEIZURE], {}, 35, True, AcuityLevel.EMERGENT),
        (
            "SAFE-007",
            [Symptom.CHEST_PAIN],
            {"heart_rate_bpm": 121},
            35,
            True,
            AcuityLevel.CRITICAL,
        ),
        ("SAFE-008", [Symptom.SHORTNESS_OF_BREATH], {}, 8, True, AcuityLevel.EMERGENT),
        (
            "SAFE-009",
            [Symptom.FEVER],
            {"temperature_c": 39.0},
            3,
            True,
            AcuityLevel.EMERGENT,
        ),
        (
            "SAFE-010",
            [Symptom.WEAKNESS],
            {"heart_rate_bpm": 121},
            75,
            False,
            AcuityLevel.EMERGENT,
        ),
        (
            "SAFE-011",
            [Symptom.SHORTNESS_OF_BREATH],
            {"oxygen_saturation_pct": None},
            35,
            False,
            AcuityLevel.EMERGENT,
        ),
        (
            "SAFE-012",
            [Symptom.ALTERED_MENTAL_STATUS],
            {},
            35,
            False,
            AcuityLevel.EMERGENT,
        ),
    ],
)
def test_individual_safety_rules(
    patient_factory,
    vitals_factory,
    rule_id,
    symptoms,
    vital_updates,
    age,
    distress,
    expected,
):
    patient = patient_factory(
        symptoms=symptoms,
        vitals=vitals_factory(**vital_updates),
        age=age,
        distress=distress,
    )
    assessment = evaluate_safety(patient)
    assert rule_id in assessment.rule_ids
    assert assessment.floor is expected
    assert assessment.reasons


def test_no_rule_defaults_to_non_urgent(patient_factory):
    assessment = evaluate_safety(patient_factory())
    assert assessment.floor is AcuityLevel.NON_URGENT
    assert assessment.hits == ()


def test_most_urgent_rule_wins(patient_factory, vitals_factory):
    patient = patient_factory(
        symptoms=[Symptom.SEIZURE, Symptom.SEVERE_BLEEDING],
        vitals=vitals_factory(consciousness=Consciousness.RESPONDS_TO_PAIN),
    )
    assessment = evaluate_safety(patient)
    assert assessment.floor is AcuityLevel.CRITICAL
    assert {"SAFE-004", "SAFE-005", "SAFE-006"} <= set(assessment.rule_ids)


def test_threshold_boundary_does_not_trigger_below_rule(
    patient_factory, vitals_factory
):
    patient = patient_factory(vitals=vitals_factory(oxygen_saturation_pct=90))
    assert "SAFE-001" not in evaluate_safety(patient).rule_ids
