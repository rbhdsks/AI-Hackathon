from __future__ import annotations

from datetime import timedelta

import pytest

from patient_triage.data.generator import generate_surge_scenario
from patient_triage.domain.enums import AcuityLevel, QueueMode, QueueState, Symptom
from patient_triage.services.ranking import RankingService


def test_invalid_ranking_configuration():
    with pytest.raises(ValueError):
        RankingService(normal_capacity=0)
    with pytest.raises(ValueError):
        RankingService(surge_multiplier=1)


def test_empty_queue_is_valid(now):
    snapshot = RankingService().rank([], now=now)
    assert snapshot.patient_count == 0
    assert snapshot.entries == []
    assert snapshot.model_status == "ready"


def test_single_patient_queue(patient_factory, now):
    snapshot = RankingService().rank([patient_factory()], now=now)
    entry = snapshot.entries[0]
    assert entry.position == 1
    assert entry.cdm_probability == pytest.approx(1)
    assert entry.context_effect == pytest.approx(0)


def test_duplicate_identifiers_rejected(patient_factory, now):
    patient = patient_factory()
    with pytest.raises(ValueError, match="duplicate"):
        RankingService().rank([patient, patient], now=now)


def test_safety_floor_beats_high_contextual_lower_acuity(
    patient_factory, vitals_factory, now
):
    critical = patient_factory(
        "SYN-CRIT",
        symptoms=[Symptom.COUGH],
        vitals=vitals_factory(oxygen_saturation_pct=88),
        pain=0,
    )
    long_wait = patient_factory(
        "SYN-WAIT",
        arrival_minutes=500,
        symptoms=[Symptom.ABDOMINAL_PAIN],
        pain=10,
    )
    snapshot = RankingService().rank([long_wait, critical], now=now)
    assert snapshot.entries[0].patient_id == "SYN-CRIT"
    assert snapshot.entries[0].acuity is AcuityLevel.CRITICAL


def test_identical_ties_are_deterministic(patient_factory, now):
    later_id = patient_factory("SYN-B")
    earlier_id = patient_factory("SYN-A")
    snapshot = RankingService().rank([later_id, earlier_id], now=now)
    assert [entry.patient_id for entry in snapshot.entries] == ["SYN-A", "SYN-B"]


def test_context_effect_changes_with_waiting_set(patient_factory, now):
    service = RankingService()
    a = patient_factory("SYN-A", arrival_minutes=80)
    b = patient_factory("SYN-B", symptoms=[Symptom.CHEST_PAIN], pain=8)
    c = patient_factory(
        "SYN-C",
        arrival_minutes=180,
        symptoms=[Symptom.SHORTNESS_OF_BREATH],
        distress=True,
    )
    first = service.rank([a, b], now=now)
    second = service.rank([a, b, c], now=now)
    first_effect = next(
        e.context_effect for e in first.entries if e.patient_id == "SYN-A"
    )
    second_effect = next(
        e.context_effect for e in second.entries if e.patient_id == "SYN-A"
    )
    assert first_effect != pytest.approx(second_effect)


def test_probabilities_form_distribution(patient_factory, now):
    patients = [
        patient_factory(f"SYN-{number}", arrival_minutes=number)
        for number in range(1, 6)
    ]
    snapshot = RankingService().rank(patients, now=now)
    assert sum(
        entry.cdm_probability or 0 for entry in snapshot.entries
    ) == pytest.approx(1)


def test_surge_mode_auto_detection(now):
    patients = generate_surge_scenario(now)
    snapshot = RankingService().rank(patients, now=now)
    assert snapshot.mode is QueueMode.SURGE
    assert snapshot.queue_pressure == 3


def test_mode_can_be_explicit(patient_factory, now):
    snapshot = RankingService().rank([patient_factory()], now=now, mode=QueueMode.SURGE)
    assert snapshot.mode is QueueMode.SURGE


def test_model_failure_uses_visible_fallback(patient_factory, now):
    service = RankingService()
    patients = [patient_factory("SYN-A"), patient_factory("SYN-B")]
    service.rank(patients, now=now)
    failed = service.rank(patients, now=now, simulate_model_failure=True)
    assert failed.model_status == "fallback"
    assert len(failed.warnings) == 2
    assert all(entry.is_stale for entry in failed.entries)
    assert all(entry.cdm_probability is None for entry in failed.entries)
    assert all(entry.state is QueueState.MANUAL_REVIEW for entry in failed.entries)


def test_new_critical_patient_is_not_lost_during_failure(
    patient_factory, vitals_factory, now
):
    service = RankingService()
    original = [patient_factory("SYN-A"), patient_factory("SYN-B")]
    service.rank(original, now=now)
    new_critical = patient_factory(
        "SYN-NEW",
        vitals=vitals_factory(oxygen_saturation_pct=85),
        symptoms=[Symptom.COUGH],
    )
    failed = service.rank(
        [*original, new_critical], now=now, simulate_model_failure=True
    )
    assert failed.entries[0].patient_id == "SYN-NEW"
    assert failed.entries[0].state is QueueState.CRITICAL_ESCALATION


def test_internal_model_error_activates_fallback(patient_factory, now, monkeypatch):
    service = RankingService()

    def fail(_matrix):
        raise ValueError("broken model")

    monkeypatch.setattr(service.cdm, "score", fail)
    snapshot = service.rank([patient_factory()], now=now)
    assert snapshot.model_status == "fallback"


def test_low_confidence_stable_patient_requires_manual_review(
    patient_factory, vitals_factory, now
):
    patient = patient_factory(
        symptoms=[Symptom.UNKNOWN],
        prior_record=False,
        pain=None,
        vitals=vitals_factory(
            heart_rate_bpm=None,
            respiratory_rate_bpm=None,
            systolic_bp_mm_hg=None,
            oxygen_saturation_pct=None,
        ),
    )
    entry = RankingService().rank([patient], now=now).entries[0]
    assert entry.confidence.value == "low"
    assert entry.state is QueueState.MANUAL_REVIEW


def test_wait_minutes_are_never_negative(patient_factory, now):
    patient = patient_factory(arrival_time=now)
    assert RankingService().rank([patient], now=now).entries[0].wait_minutes == 0


def test_future_arrival_is_rejected(patient_factory, now):
    patient = patient_factory(arrival_time=now + timedelta(seconds=1))
    with pytest.raises(ValueError, match="future"):
        RankingService().rank([patient], now=now)
