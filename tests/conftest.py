from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from patient_triage.domain.enums import AcuityLevel, Consciousness, Symptom
from patient_triage.domain.patient import Patient, VitalSigns


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 8, 25, 12, 0, tzinfo=UTC)


@pytest.fixture
def patient_factory(now: datetime) -> Callable[..., Patient]:
    def factory(
        patient_id: str = "SYN-TEST",
        *,
        age: float = 35,
        arrival_minutes: float = 10,
        symptoms: list[Symptom] | None = None,
        vitals: VitalSigns | None = None,
        previous_vitals: VitalSigns | None = None,
        pain: int | None = 3,
        distress: bool = False,
        prior_record: bool = True,
        expected: AcuityLevel | None = None,
        **extra: Any,
    ) -> Patient:
        observation = vitals or VitalSigns(
            heart_rate_bpm=82,
            respiratory_rate_bpm=16,
            systolic_bp_mm_hg=122,
            diastolic_bp_mm_hg=78,
            oxygen_saturation_pct=98,
            temperature_c=36.8,
            consciousness=Consciousness.ALERT,
            recorded_at=now - timedelta(minutes=2),
        )
        values: dict[str, Any] = {
            "patient_id": patient_id,
            "age_years": age,
            "arrival_time": now - timedelta(minutes=arrival_minutes),
            "symptoms": symptoms or [Symptom.MINOR_INJURY],
            "pain_score": pain,
            "observed_distress": distress,
            "has_prior_record": prior_record,
            "vitals": observation,
            "previous_vitals": previous_vitals,
            "expected_acuity": expected,
        }
        values.update(extra)
        return Patient(**values)

    return factory


@pytest.fixture
def vitals_factory(now: datetime) -> Callable[..., VitalSigns]:
    def factory(**updates: Any) -> VitalSigns:
        values: dict[str, Any] = {
            "heart_rate_bpm": 82,
            "respiratory_rate_bpm": 16,
            "systolic_bp_mm_hg": 122,
            "diastolic_bp_mm_hg": 78,
            "oxygen_saturation_pct": 98,
            "temperature_c": 36.8,
            "consciousness": Consciousness.ALERT,
            "recorded_at": now - timedelta(minutes=2),
        }
        values.update(updates)
        return VitalSigns(**values)

    return factory
