from __future__ import annotations

from datetime import timedelta

import numpy as np
import pytest

from patient_triage.domain.enums import AcuityLevel, QueueMode, Symptom
from patient_triage.models.features import (
    FEATURE_NAMES,
    extract_features,
    physiology_risk,
)
from patient_triage.models.urgency import TransparentUrgencyModel


def test_features_are_bounded_and_named(patient_factory, now):
    features = extract_features(patient_factory(), now)
    assert features.values.shape == (len(FEATURE_NAMES),)
    assert np.isfinite(features.values).all()
    assert ((features.values >= 0) & (features.values <= 1)).all()
    assert set(features.as_dict()) == set(FEATURE_NAMES)


def test_future_arrival_is_rejected(patient_factory, now):
    patient = patient_factory(arrival_time=now + timedelta(seconds=1))
    with pytest.raises(ValueError, match="future"):
        extract_features(patient, now)


def test_zero_history_and_ambiguity_raise_uncertainty(patient_factory, now):
    complete = extract_features(patient_factory(), now).as_dict()["uncertainty"]
    ambiguous = extract_features(
        patient_factory(symptoms=[Symptom.UNKNOWN], prior_record=False, pain=None),
        now,
    )
    assert ambiguous.as_dict()["uncertainty"] > complete
    assert "missing or ambiguous" in " ".join(ambiguous.explanations)


def test_missing_vitals_are_not_imputed_as_normal(patient_factory, vitals_factory, now):
    patient = patient_factory(
        vitals=vitals_factory(
            heart_rate_bpm=None,
            respiratory_rate_bpm=None,
            systolic_bp_mm_hg=None,
            diastolic_bp_mm_hg=None,
            oxygen_saturation_pct=None,
            temperature_c=None,
            consciousness=None,
        )
    )
    features = extract_features(patient, now)
    assert len(features.missing_information) == 6
    assert features.as_dict()["uncertainty"] >= 0.65


def test_deterioration_feature_uses_previous_observation(
    patient_factory, vitals_factory, now
):
    previous = vitals_factory(
        recorded_at=now - timedelta(minutes=20), oxygen_saturation_pct=98
    )
    current = vitals_factory(
        recorded_at=now - timedelta(minutes=1),
        oxygen_saturation_pct=90,
        heart_rate_bpm=130,
    )
    patient = patient_factory(vitals=current, previous_vitals=previous)
    assert extract_features(patient, now).as_dict()["deterioration"] > 0


def test_waiting_feature_is_more_sensitive_in_surge(patient_factory, now):
    patient = patient_factory(arrival_minutes=60)
    normal = extract_features(patient, now, QueueMode.NORMAL).as_dict()["waiting"]
    surge = extract_features(patient, now, QueueMode.SURGE).as_dict()["waiting"]
    assert surge > normal


def test_age_adjusted_ranges_change_physiology(patient_factory, vitals_factory):
    observed = vitals_factory(heart_rate_bpm=135, respiratory_rate_bpm=35)
    child = patient_factory(age=3, vitals=observed)
    adult = patient_factory(age=35, vitals=observed)
    assert physiology_risk(child) < physiology_risk(adult)


def test_vulnerability_feature_age_groups(patient_factory, now):
    assert extract_features(patient_factory(age=3), now).as_dict()["vulnerability"] == 1
    assert (
        extract_features(patient_factory(age=12), now).as_dict()["vulnerability"] == 0.6
    )
    assert (
        extract_features(patient_factory(age=40), now).as_dict()["vulnerability"] == 0
    )
    assert (
        extract_features(patient_factory(age=80), now).as_dict()["vulnerability"] == 1
    )


def test_urgency_model_score_and_dimension(patient_factory, now):
    model = TransparentUrgencyModel()
    features = extract_features(patient_factory(), now)
    assert np.isfinite(model.score(features))
    bad = type(features)(np.zeros(2), (), ())
    with pytest.raises(ValueError, match="dimension"):
        model.score(bad)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (5.0, AcuityLevel.EMERGENT),
        (4.5, AcuityLevel.EMERGENT),
        (1.4, AcuityLevel.URGENT),
        (0.65, AcuityLevel.LESS_URGENT),
        (0.64, AcuityLevel.NON_URGENT),
    ],
)
def test_urgency_classification_thresholds(score, expected):
    assert TransparentUrgencyModel.classify(score) is expected


def test_non_finite_urgency_score_rejected():
    with pytest.raises(ValueError, match="finite"):
        TransparentUrgencyModel.classify(float("nan"))
