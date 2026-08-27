"""Fail-safe escalation rules evaluated before any statistical ranking."""

from __future__ import annotations

from dataclasses import dataclass

from patient_triage.domain.enums import AcuityLevel, Consciousness, Symptom
from patient_triage.domain.patient import Patient


@dataclass(frozen=True, slots=True)
class RuleHit:
    rule_id: str
    acuity: AcuityLevel
    reason: str


@dataclass(frozen=True, slots=True)
class SafetyAssessment:
    floor: AcuityLevel
    hits: tuple[RuleHit, ...]

    @property
    def reasons(self) -> list[str]:
        return [hit.reason for hit in self.hits]

    @property
    def rule_ids(self) -> list[str]:
        return [hit.rule_id for hit in self.hits]


def evaluate_safety(patient: Patient) -> SafetyAssessment:
    """Evaluate conservative, illustrative red flags.

    These thresholds exist only to demonstrate software behavior on synthetic
    cases. They are not a validated triage protocol.
    """

    vitals = patient.vitals
    symptoms = set(patient.symptoms)
    hits: list[RuleHit] = []

    def hit(rule_id: str, acuity: AcuityLevel, reason: str) -> None:
        hits.append(RuleHit(rule_id=rule_id, acuity=acuity, reason=reason))

    if vitals.oxygen_saturation_pct is not None and vitals.oxygen_saturation_pct < 90:
        hit(
            "SAFE-001",
            AcuityLevel.CRITICAL,
            "oxygen saturation is below the prototype red-flag threshold",
        )

    if vitals.systolic_bp_mm_hg is not None and vitals.systolic_bp_mm_hg < 90:
        hit(
            "SAFE-002",
            AcuityLevel.CRITICAL,
            "systolic blood pressure is below the prototype red-flag threshold",
        )

    if vitals.consciousness is Consciousness.UNRESPONSIVE:
        hit("SAFE-003", AcuityLevel.CRITICAL, "patient is recorded as unresponsive")
    elif vitals.consciousness is Consciousness.RESPONDS_TO_PAIN:
        hit(
            "SAFE-004", AcuityLevel.EMERGENT, "consciousness is responsive only to pain"
        )

    if Symptom.SEVERE_BLEEDING in symptoms:
        hit("SAFE-005", AcuityLevel.CRITICAL, "severe bleeding is recorded")

    if Symptom.SEIZURE in symptoms:
        hit("SAFE-006", AcuityLevel.EMERGENT, "seizure is recorded")

    chest_pain_abnormal_vital = Symptom.CHEST_PAIN in symptoms and (
        (vitals.oxygen_saturation_pct is not None and vitals.oxygen_saturation_pct < 94)
        or (vitals.systolic_bp_mm_hg is not None and vitals.systolic_bp_mm_hg < 100)
        or (vitals.heart_rate_bpm is not None and vitals.heart_rate_bpm > 120)
    )
    if chest_pain_abnormal_vital:
        hit(
            "SAFE-007",
            AcuityLevel.CRITICAL,
            "chest pain is accompanied by an abnormal recorded vital",
        )

    if (
        patient.age_years < 12
        and Symptom.SHORTNESS_OF_BREATH in symptoms
        and patient.observed_distress
    ):
        hit(
            "SAFE-008",
            AcuityLevel.EMERGENT,
            "pediatric respiratory symptoms with observed distress require escalation",
        )

    if (
        patient.age_years < 5
        and Symptom.FEVER in symptoms
        and vitals.temperature_c is not None
        and vitals.temperature_c >= 39
        and patient.observed_distress
    ):
        hit(
            "SAFE-009",
            AcuityLevel.EMERGENT,
            "young child with high recorded temperature and distress",
        )

    atypical_geriatric_signs = {Symptom.WEAKNESS, Symptom.DIZZINESS} & symptoms
    if (
        patient.age_years >= 65
        and atypical_geriatric_signs
        and (
            (vitals.heart_rate_bpm is not None and vitals.heart_rate_bpm > 120)
            or (vitals.systolic_bp_mm_hg is not None and vitals.systolic_bp_mm_hg < 100)
        )
    ):
        hit(
            "SAFE-010",
            AcuityLevel.EMERGENT,
            "geriatric atypical symptoms are accompanied by an abnormal vital",
        )

    high_risk_symptoms = {
        Symptom.CHEST_PAIN,
        Symptom.SHORTNESS_OF_BREATH,
        Symptom.ALTERED_MENTAL_STATUS,
        Symptom.SEVERE_BLEEDING,
    }
    missing_critical_measurement = (
        vitals.oxygen_saturation_pct is None or vitals.systolic_bp_mm_hg is None
    )
    if symptoms & high_risk_symptoms and missing_critical_measurement:
        hit(
            "SAFE-011",
            AcuityLevel.EMERGENT,
            "high-risk symptom has missing critical measurements; escalate under uncertainty",
        )

    if Symptom.ALTERED_MENTAL_STATUS in symptoms:
        hit("SAFE-012", AcuityLevel.EMERGENT, "altered mental status is recorded")

    floor = min((item.acuity for item in hits), default=AcuityLevel.NON_URGENT)
    return SafetyAssessment(floor=floor, hits=tuple(hits))
