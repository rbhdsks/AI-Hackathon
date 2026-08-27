"""Feature extraction shared by the urgency and CDM layers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np

from patient_triage.domain.enums import AgeGroup, Consciousness, QueueMode, Symptom
from patient_triage.domain.patient import Patient, VitalSigns, require_aware

FEATURE_NAMES = (
    "physiology_risk",
    "symptom_risk",
    "pain",
    "waiting",
    "deterioration",
    "uncertainty",
    "vulnerability",
)


@dataclass(frozen=True, slots=True)
class FeatureVector:
    values: np.ndarray
    explanations: tuple[str, ...]
    missing_information: tuple[str, ...]

    def as_dict(self) -> dict[str, float]:
        return dict(zip(FEATURE_NAMES, self.values, strict=True))


def _outside_range(value: float | None, low: float, high: float, scale: float) -> float:
    if value is None:
        return 0.0
    if value < low:
        return min((low - value) / scale, 1.0)
    if value > high:
        return min((value - high) / scale, 1.0)
    return 0.0


def _age_adjusted_ranges(
    patient: Patient,
) -> tuple[tuple[float, float], tuple[float, float], float]:
    age = patient.age_years
    if age < 1:
        return (100, 160), (30, 60), 70
    if age < 5:
        return (80, 140), (20, 40), 75
    if age < 12:
        return (70, 120), (18, 30), 80
    if age < 18:
        return (60, 110), (12, 25), 90
    return (60, 100), (12, 20), 90


def physiology_risk(patient: Patient, vitals: VitalSigns | None = None) -> float:
    observed = vitals or patient.vitals
    heart_range, respiratory_range, low_systolic = _age_adjusted_ranges(patient)
    components = [
        _outside_range(observed.heart_rate_bpm, *heart_range, 50),
        _outside_range(observed.respiratory_rate_bpm, *respiratory_range, 25),
        _outside_range(observed.systolic_bp_mm_hg, low_systolic, 180, 45),
        _outside_range(observed.oxygen_saturation_pct, 95, 100, 10),
        _outside_range(observed.temperature_c, 36, 37.8, 5),
    ]
    consciousness_risk = {
        None: 0.0,
        Consciousness.ALERT: 0.0,
        Consciousness.RESPONDS_TO_VOICE: 0.45,
        Consciousness.RESPONDS_TO_PAIN: 0.8,
        Consciousness.UNRESPONSIVE: 1.0,
    }[observed.consciousness]
    components.append(consciousness_risk)
    maximum = max(components, default=0.0)
    mean = sum(components) / len(components)
    return float(min(0.75 * maximum + 0.5 * mean, 1.0))


_SYMPTOM_RISK: dict[Symptom, float] = {
    Symptom.SEVERE_BLEEDING: 1.0,
    Symptom.ALTERED_MENTAL_STATUS: 0.95,
    Symptom.SEIZURE: 0.95,
    Symptom.CHEST_PAIN: 0.85,
    Symptom.SHORTNESS_OF_BREATH: 0.85,
    Symptom.TRAUMA: 0.7,
    Symptom.WEAKNESS: 0.5,
    Symptom.DIZZINESS: 0.45,
    Symptom.ABDOMINAL_PAIN: 0.45,
    Symptom.HEADACHE: 0.4,
    Symptom.VOMITING: 0.35,
    Symptom.FEVER: 0.35,
    Symptom.UNKNOWN: 0.4,
    Symptom.COUGH: 0.2,
    Symptom.RASH: 0.15,
    Symptom.MINOR_INJURY: 0.1,
}


def extract_features(
    patient: Patient,
    now: datetime,
    mode: QueueMode = QueueMode.NORMAL,
) -> FeatureVector:
    """Create a bounded, finite seven-dimensional patient representation."""

    now = require_aware(now, "now")
    if patient.arrival_time > now:
        raise ValueError("arrival time cannot be in the future")

    current_physiology = physiology_risk(patient)
    symptom_risk = max(_SYMPTOM_RISK[item] for item in patient.symptoms)
    pain = (patient.pain_score or 0) / 10
    wait_minutes = (now - patient.arrival_time).total_seconds() / 60
    wait_scale = 90 if mode is QueueMode.SURGE else 180
    waiting = min(wait_minutes / wait_scale, 1.0)

    deterioration = 0.0
    if patient.previous_vitals is not None:
        previous = physiology_risk(patient, patient.previous_vitals)
        deterioration = min(max(current_physiology - previous, 0.0) * 2, 1.0)

    missing = patient.vitals.missing_measurements()
    uncertainty = len(missing) / 6 * 0.65
    if not patient.has_prior_record:
        uncertainty += 0.15
    if Symptom.UNKNOWN in patient.symptoms:
        uncertainty += 0.2
    if patient.pain_score is None:
        uncertainty += 0.05
    uncertainty = min(uncertainty, 1.0)

    if patient.age_years < 5 or patient.age_years >= 75:
        vulnerability = 1.0
    elif patient.age_group in {AgeGroup.PEDIATRIC, AgeGroup.GERIATRIC}:
        vulnerability = 0.6
    else:
        vulnerability = 0.0

    explanations: list[str] = []
    if current_physiology >= 0.35:
        explanations.append("recorded vital signs contribute to urgency")
    if symptom_risk >= 0.7:
        explanations.append("a high-risk symptom category is present")
    if waiting >= 0.5:
        explanations.append("waiting time contributes to reassessment priority")
    if deterioration >= 0.2:
        explanations.append(
            "recorded vitals have worsened since the previous observation"
        )
    if uncertainty >= 0.35:
        explanations.append("missing or ambiguous information increases uncertainty")
    if vulnerability > 0:
        explanations.append(f"age-aware {patient.age_group.value} adjustment is active")

    values = np.asarray(
        [
            current_physiology,
            symptom_risk,
            pain,
            waiting,
            deterioration,
            uncertainty,
            vulnerability,
        ],
        dtype=np.float64,
    )
    if not np.isfinite(values).all():
        raise ValueError("features must be finite")
    return FeatureVector(values, tuple(explanations), tuple(missing))
