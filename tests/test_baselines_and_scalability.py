from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from patient_triage.data.generator import generate_scenario
from patient_triage.domain.hospital import load_hospital_profile
from patient_triage.evaluation.baselines import BaselineStrategy, compare_baselines
from patient_triage.evaluation.scalability import (
    benchmark_scalability,
    expand_synthetic_patients,
)
from patient_triage.services.ranking import RankingService


def test_all_six_baselines_and_empty_queue(now) -> None:
    profile = load_hospital_profile(Path("configs/district_hospital.json"))
    patients = generate_scenario("normal", now)
    snapshot = RankingService().rank(patients, now=now)
    report = compare_baselines(patients, snapshot, profile)
    assert [item.strategy for item in report.results] == list(BaselineStrategy)
    assert all(item.mean_additional_wait_minutes >= 0 for item in report.results)
    assert all(item.completed_within_120_minutes <= 20 for item in report.results)
    assert "does not establish clinical effectiveness" in report.limitation

    empty = RankingService().rank([], now=now)
    empty_report = compare_baselines([], empty, profile)
    assert all(item.mean_additional_wait_minutes == 0 for item in empty_report.results)
    assert all(item.high_risk_top_five_rate is None for item in empty_report.results)


def test_expand_and_scalability_validation(now) -> None:
    templates = generate_scenario("normal", now)
    expanded = expand_synthetic_patients(templates, 45)
    assert len(expanded) == 45
    assert len({patient.patient_id for patient in expanded}) == 45
    assert expanded[20].arrival_time < expanded[0].arrival_time
    with pytest.raises(ValueError, match="at least one"):
        expand_synthetic_patients([], 2)
    with pytest.raises(ValueError, match="at least one"):
        expand_synthetic_patients(templates, 0)

    report = benchmark_scalability(
        templates,
        patient_counts=(5, 10),
        repetitions=2,
        now=now,
    )
    assert [point.patient_count for point in report.points] == [5, 10]
    assert all(point.throughput_patients_per_second > 0 for point in report.points)
    with pytest.raises(ValueError, match="repetitions"):
        benchmark_scalability(templates, repetitions=0, now=now)
    with pytest.raises(ValueError, match="patient_counts"):
        benchmark_scalability(templates, patient_counts=(), now=now)
    with pytest.raises(ValueError, match="timezone"):
        benchmark_scalability(
            templates,
            patient_counts=(5,),
            repetitions=1,
            now=datetime(2026, 8, 25, 12, 0),
        )
