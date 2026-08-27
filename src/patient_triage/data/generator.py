"""Deterministic synthetic scenarios for the hackathon demonstration."""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from patient_triage.domain.enums import AcuityLevel, Consciousness, Symptom
from patient_triage.domain.patient import Patient, VitalSigns, require_aware


def _vitals(
    now: datetime,
    *,
    minutes_ago: float = 2,
    heart_rate: int | None = 82,
    respiratory_rate: int | None = 16,
    systolic: int | None = 122,
    diastolic: int | None = 78,
    oxygen: float | None = 98,
    temperature: float | None = 36.8,
    consciousness: Consciousness | None = Consciousness.ALERT,
) -> VitalSigns:
    return VitalSigns(
        heart_rate_bpm=heart_rate,
        respiratory_rate_bpm=respiratory_rate,
        systolic_bp_mm_hg=systolic,
        diastolic_bp_mm_hg=diastolic,
        oxygen_saturation_pct=oxygen,
        temperature_c=temperature,
        consciousness=consciousness,
        recorded_at=now - timedelta(minutes=minutes_ago),
    )


def _patient(
    now: datetime,
    patient_id: str,
    *,
    age: float,
    arrived_minutes_ago: float,
    symptoms: list[Symptom],
    vitals: VitalSigns,
    pain: int | None,
    distress: bool = False,
    prior_record: bool = True,
    previous_vitals: VitalSigns | None = None,
    expected: AcuityLevel,
    tags: list[str] | None = None,
) -> Patient:
    return Patient(
        patient_id=patient_id,
        age_years=age,
        arrival_time=now - timedelta(minutes=arrived_minutes_ago),
        symptoms=symptoms,
        pain_score=pain,
        observed_distress=distress,
        has_prior_record=prior_record,
        vitals=vitals,
        previous_vitals=previous_vitals,
        expected_acuity=expected,
        scenario_tags=tags or [],
    )


def generate_normal_scenario(now: datetime) -> list[Patient]:
    """Return 20 curated cases covering the Round 2 minimum expectations."""

    now = require_aware(now, "now")
    patients = [
        _patient(
            now,
            "SYN-001",
            age=54,
            arrived_minutes_ago=8,
            symptoms=[Symptom.SHORTNESS_OF_BREATH],
            vitals=_vitals(now, heart_rate=132, respiratory_rate=32, oxygen=86),
            pain=7,
            distress=True,
            expected=AcuityLevel.CRITICAL,
            tags=["critical", "respiratory"],
        ),
        _patient(
            now,
            "SYN-002",
            age=61,
            arrived_minutes_ago=12,
            symptoms=[Symptom.CHEST_PAIN],
            vitals=_vitals(now, heart_rate=118, systolic=82, diastolic=50, oxygen=93),
            pain=9,
            distress=True,
            expected=AcuityLevel.CRITICAL,
            tags=["critical", "chest_pain"],
        ),
        _patient(
            now,
            "SYN-003",
            age=39,
            arrived_minutes_ago=5,
            symptoms=[Symptom.TRAUMA],
            vitals=_vitals(now, consciousness=Consciousness.UNRESPONSIVE),
            pain=None,
            distress=True,
            expected=AcuityLevel.CRITICAL,
            tags=["critical", "altered_consciousness"],
        ),
        _patient(
            now,
            "SYN-004",
            age=27,
            arrived_minutes_ago=6,
            symptoms=[Symptom.SEVERE_BLEEDING, Symptom.TRAUMA],
            vitals=_vitals(now, heart_rate=126, systolic=96, diastolic=62),
            pain=8,
            distress=True,
            expected=AcuityLevel.CRITICAL,
            tags=["critical", "bleeding"],
        ),
        _patient(
            now,
            "SYN-005",
            age=3,
            arrived_minutes_ago=18,
            symptoms=[Symptom.FEVER],
            vitals=_vitals(now, heart_rate=148, respiratory_rate=36, temperature=39.4),
            pain=4,
            distress=True,
            prior_record=False,
            expected=AcuityLevel.EMERGENT,
            tags=["pediatric", "zero_history"],
        ),
        _patient(
            now,
            "SYN-006",
            age=8,
            arrived_minutes_ago=15,
            symptoms=[Symptom.SHORTNESS_OF_BREATH, Symptom.COUGH],
            vitals=_vitals(now, heart_rate=122, respiratory_rate=34, oxygen=93),
            pain=3,
            distress=True,
            expected=AcuityLevel.EMERGENT,
            tags=["pediatric", "respiratory"],
        ),
        _patient(
            now,
            "SYN-007",
            age=78,
            arrived_minutes_ago=22,
            symptoms=[Symptom.WEAKNESS, Symptom.DIZZINESS],
            vitals=_vitals(now, heart_rate=132, systolic=98, diastolic=64),
            pain=2,
            expected=AcuityLevel.EMERGENT,
            tags=["geriatric", "atypical_presentation"],
        ),
        _patient(
            now,
            "SYN-008",
            age=31,
            arrived_minutes_ago=9,
            symptoms=[Symptom.SEIZURE],
            vitals=_vitals(
                now, heart_rate=112, consciousness=Consciousness.RESPONDS_TO_VOICE
            ),
            pain=None,
            distress=True,
            expected=AcuityLevel.EMERGENT,
            tags=["neurologic"],
        ),
        _patient(
            now,
            "SYN-009",
            age=46,
            arrived_minutes_ago=35,
            symptoms=[Symptom.CHEST_PAIN],
            vitals=_vitals(now, heart_rate=98, systolic=124, diastolic=80, oxygen=97),
            pain=6,
            expected=AcuityLevel.URGENT,
            tags=["chest_pain"],
        ),
        _patient(
            now,
            "SYN-010",
            age=24,
            arrived_minutes_ago=44,
            symptoms=[Symptom.ABDOMINAL_PAIN, Symptom.VOMITING],
            vitals=_vitals(now, heart_rate=105, temperature=38.0),
            pain=7,
            expected=AcuityLevel.URGENT,
            tags=["abdominal"],
        ),
        _patient(
            now,
            "SYN-011",
            age=42,
            arrived_minutes_ago=25,
            symptoms=[Symptom.UNKNOWN, Symptom.DIZZINESS],
            vitals=_vitals(
                now,
                heart_rate=94,
                systolic=None,
                diastolic=None,
                oxygen=None,
                temperature=None,
            ),
            pain=None,
            prior_record=False,
            expected=AcuityLevel.URGENT,
            tags=["ambiguous", "zero_history", "missing_vitals"],
        ),
        _patient(
            now,
            "SYN-012",
            age=19,
            arrived_minutes_ago=50,
            symptoms=[Symptom.FEVER, Symptom.VOMITING],
            vitals=_vitals(now, heart_rate=104, temperature=38.4),
            pain=4,
            prior_record=False,
            expected=AcuityLevel.URGENT,
            tags=["zero_history"],
        ),
        _patient(
            now,
            "SYN-013",
            age=67,
            arrived_minutes_ago=55,
            symptoms=[Symptom.HEADACHE],
            vitals=_vitals(now, systolic=172, diastolic=96),
            pain=6,
            expected=AcuityLevel.URGENT,
            tags=["geriatric"],
        ),
        _patient(
            now,
            "SYN-014",
            age=34,
            arrived_minutes_ago=70,
            symptoms=[Symptom.TRAUMA],
            vitals=_vitals(now, heart_rate=92),
            pain=5,
            expected=AcuityLevel.LESS_URGENT,
            tags=["stable_trauma"],
        ),
        _patient(
            now,
            "SYN-015",
            age=29,
            arrived_minutes_ago=80,
            symptoms=[Symptom.COUGH],
            vitals=_vitals(now, temperature=37.5),
            pain=2,
            expected=AcuityLevel.LESS_URGENT,
            tags=["respiratory"],
        ),
        _patient(
            now,
            "SYN-016",
            age=51,
            arrived_minutes_ago=92,
            symptoms=[Symptom.RASH],
            vitals=_vitals(now),
            pain=3,
            expected=AcuityLevel.LESS_URGENT,
            tags=["stable"],
        ),
        _patient(
            now,
            "SYN-017",
            age=73,
            arrived_minutes_ago=105,
            symptoms=[Symptom.DIZZINESS],
            vitals=_vitals(now, heart_rate=88, systolic=118, diastolic=74),
            pain=1,
            expected=AcuityLevel.LESS_URGENT,
            tags=["geriatric"],
        ),
        _patient(
            now,
            "SYN-018",
            age=22,
            arrived_minutes_ago=120,
            symptoms=[Symptom.MINOR_INJURY],
            vitals=_vitals(now),
            pain=3,
            expected=AcuityLevel.NON_URGENT,
            tags=["minor"],
        ),
        _patient(
            now,
            "SYN-019",
            age=58,
            arrived_minutes_ago=48,
            symptoms=[Symptom.SHORTNESS_OF_BREATH],
            previous_vitals=_vitals(
                now,
                minutes_ago=22,
                heart_rate=94,
                respiratory_rate=18,
                systolic=128,
                diastolic=80,
                oxygen=97,
            ),
            vitals=_vitals(
                now,
                minutes_ago=2,
                heart_rate=129,
                respiratory_rate=29,
                systolic=101,
                diastolic=68,
                oxygen=91,
            ),
            pain=5,
            distress=True,
            expected=AcuityLevel.EMERGENT,
            tags=["deteriorating"],
        ),
        _patient(
            now,
            "SYN-020",
            age=37,
            arrived_minutes_ago=150,
            symptoms=[Symptom.MINOR_INJURY],
            vitals=_vitals(now),
            pain=2,
            expected=AcuityLevel.NON_URGENT,
            tags=["unsafe_wait"],
        ),
    ]
    return patients


def generate_surge_scenario(now: datetime, seed: int = 20260825) -> list[Patient]:
    """Return a deterministic 60-patient, three-times-normal scenario."""

    now = require_aware(now, "now")
    patients = generate_normal_scenario(now)
    rng = np.random.default_rng(seed)
    low_risk_symptoms = [
        Symptom.MINOR_INJURY,
        Symptom.COUGH,
        Symptom.RASH,
        Symptom.HEADACHE,
        Symptom.VOMITING,
        Symptom.ABDOMINAL_PAIN,
    ]
    for number in range(21, 61):
        symptom = low_risk_symptoms[(number - 21) % len(low_risk_symptoms)]
        moderate = number % 9 == 0
        missing = number % 11 == 0
        age = float(rng.integers(18, 85))
        if number == 31:
            age = 2.0
        expected = AcuityLevel.URGENT if moderate else AcuityLevel.LESS_URGENT
        if symptom in {Symptom.MINOR_INJURY, Symptom.RASH} and not moderate:
            expected = AcuityLevel.NON_URGENT
        patients.append(
            _patient(
                now,
                f"SYN-{number:03d}",
                age=age,
                arrived_minutes_ago=float(rng.integers(1, 180)),
                symptoms=[symptom],
                vitals=_vitals(
                    now,
                    minutes_ago=float(rng.integers(1, 20)),
                    heart_rate=int(rng.integers(72, 116)) if not missing else None,
                    respiratory_rate=int(rng.integers(14, 26)),
                    systolic=int(rng.integers(104, 158)) if not missing else None,
                    diastolic=int(rng.integers(60, 94)) if not missing else None,
                    oxygen=float(rng.integers(94, 100)) if not missing else None,
                    temperature=float(rng.uniform(36.2, 38.3)),
                ),
                pain=int(rng.integers(1, 8)),
                distress=moderate,
                prior_record=number % 2 == 0,
                expected=expected,
                tags=["surge_generated"] + (["missing_vitals"] if missing else []),
            )
        )
    return patients


def generate_scenario(name: str, now: datetime) -> list[Patient]:
    normalized = name.strip().lower()
    if normalized == "normal":
        return generate_normal_scenario(now)
    if normalized == "surge":
        return generate_surge_scenario(now)
    raise ValueError("scenario must be 'normal' or 'surge'")


def deteriorated_vitals(patient: Patient, now: datetime) -> VitalSigns:
    """Produce a visibly worse synthetic observation for an existing patient."""

    now = require_aware(now, "now")
    current = patient.vitals
    return VitalSigns(
        heart_rate_bpm=min((current.heart_rate_bpm or 90) + 35, 300),
        respiratory_rate_bpm=min((current.respiratory_rate_bpm or 18) + 10, 100),
        systolic_bp_mm_hg=max((current.systolic_bp_mm_hg or 120) - 25, 30),
        diastolic_bp_mm_hg=max((current.diastolic_bp_mm_hg or 80) - 15, 10),
        oxygen_saturation_pct=max((current.oxygen_saturation_pct or 97) - 8, 0),
        temperature_c=current.temperature_c,
        consciousness=current.consciousness or Consciousness.ALERT,
        recorded_at=now,
    )
