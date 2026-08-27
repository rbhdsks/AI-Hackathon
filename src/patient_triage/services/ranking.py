"""Safety-constrained CDM queue ranking with a rule-only fallback."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import RLock

import numpy as np

from patient_triage.domain.enums import (
    AcuityLevel,
    ConfidenceLevel,
    QueueMode,
    QueueState,
)
from patient_triage.domain.patient import Patient, require_aware
from patient_triage.domain.queue import QueueEntry, QueueSnapshot
from patient_triage.models.cdm import CDMOutput, FeatureContextDependentModel
from patient_triage.models.confidence import assess_confidence
from patient_triage.models.features import FeatureVector, extract_features
from patient_triage.models.urgency import TransparentUrgencyModel
from patient_triage.rules.safety_rules import SafetyAssessment, evaluate_safety
from patient_triage.services.monitoring import assess_monitoring


@dataclass(slots=True)
class _Candidate:
    patient: Patient
    features: FeatureVector
    safety: SafetyAssessment
    base_score: float
    acuity: AcuityLevel


class RankingService:
    def __init__(
        self,
        *,
        normal_capacity: int = 20,
        surge_multiplier: int = 3,
        model_version: str = "feature-cdm-v1",
    ) -> None:
        if normal_capacity < 1 or surge_multiplier < 2:
            raise ValueError(
                "capacity must be positive and surge multiplier at least two"
            )
        self.normal_capacity = normal_capacity
        self.surge_multiplier = surge_multiplier
        self.urgency_model = TransparentUrgencyModel()
        self.cdm = FeatureContextDependentModel(version=model_version)
        self._last_good_positions: dict[str, int] = {}
        self._lock = RLock()

    def _mode_for(self, patient_count: int, requested: QueueMode | None) -> QueueMode:
        if requested is not None:
            return requested
        threshold = self.normal_capacity * self.surge_multiplier
        return QueueMode.SURGE if patient_count >= threshold else QueueMode.NORMAL

    def rank(
        self,
        patients: list[Patient],
        *,
        now: datetime,
        mode: QueueMode | None = None,
        simulate_model_failure: bool = False,
    ) -> QueueSnapshot:
        now = require_aware(now, "now")
        patient_ids = [patient.patient_id for patient in patients]
        if len(patient_ids) != len(set(patient_ids)):
            raise ValueError("queue cannot contain duplicate patient identifiers")

        queue_mode = self._mode_for(len(patients), mode)
        pressure = len(patients) / self.normal_capacity
        if not patients:
            return QueueSnapshot(
                generated_at=now,
                mode=queue_mode,
                model_status="ready",
                model_version=self.cdm.version,
                patient_count=0,
                queue_pressure=0,
                entries=[],
                warnings=[],
            )

        candidates: list[_Candidate] = []
        for patient in patients:
            features = extract_features(patient, now, queue_mode)
            safety = evaluate_safety(patient)
            base_score = self.urgency_model.score(features)
            model_acuity = self.urgency_model.classify(base_score)
            acuity = min(safety.floor, model_acuity)
            candidates.append(_Candidate(patient, features, safety, base_score, acuity))

        warnings: list[str] = []
        model_available = not simulate_model_failure
        output: CDMOutput | None = None
        if model_available:
            try:
                feature_matrix = np.vstack(
                    [candidate.features.values for candidate in candidates]
                )
                output = self.cdm.score(feature_matrix)
            except (FloatingPointError, ValueError):
                model_available = False

        if not model_available:
            warnings.extend(
                [
                    "CDM unavailable: rule-only fallback is active",
                    "All recommendations require manual review until the model recovers",
                ]
            )

        if output is not None:
            ordering = sorted(
                range(len(candidates)),
                key=lambda index: (
                    int(candidates[index].acuity),
                    -float(output.utilities[index]),
                    candidates[index].patient.arrival_time,
                    candidates[index].patient.patient_id,
                ),
            )
        else:
            with self._lock:
                last_positions = dict(self._last_good_positions)
            ordering = sorted(
                range(len(candidates)),
                key=lambda index: (
                    int(candidates[index].acuity),
                    last_positions.get(candidates[index].patient.patient_id, 10**9),
                    candidates[index].patient.arrival_time,
                    candidates[index].patient.patient_id,
                ),
            )

        entries: list[QueueEntry] = []
        for position, candidate_index in enumerate(ordering, start=1):
            candidate = candidates[candidate_index]
            confidence = assess_confidence(
                candidate.patient,
                now,
                queue_mode,
                model_available=model_available,
            )
            monitoring = assess_monitoring(
                candidate.patient, candidate.acuity, now, queue_mode
            )
            state = monitoring.state
            action = monitoring.recommended_action
            alerts = list(monitoring.alerts)
            if confidence.level is ConfidenceLevel.LOW and state is QueueState.STABLE:
                state = QueueState.MANUAL_REVIEW
                action = (
                    "Complete missing information and request clinician reassessment"
                )
                alerts.append("low-confidence recommendation requires review")
            if not model_available and state not in {
                QueueState.CRITICAL_ESCALATION,
                QueueState.DETERIORATING,
            }:
                state = QueueState.MANUAL_REVIEW
                action = "Use rule-only order and perform manual reassessment"

            reasons = list(candidate.safety.reasons)
            reasons.extend(candidate.features.explanations)
            reasons.append(
                f"transparent patient-level urgency score: {candidate.base_score:.3f}"
            )
            if output is not None:
                context_value = float(output.context_effects[candidate_index])
                reasons.append(
                    f"current waiting-set context changed CDM utility by {context_value:+.3f}"
                )

            entries.append(
                QueueEntry(
                    position=position,
                    patient_id=candidate.patient.patient_id,
                    acuity=candidate.acuity,
                    acuity_label=candidate.acuity.label,
                    safety_floor=candidate.safety.floor,
                    cdm_probability=(
                        float(output.probabilities[candidate_index])
                        if output is not None
                        else None
                    ),
                    cdm_utility=(
                        float(output.utilities[candidate_index])
                        if output is not None
                        else None
                    ),
                    base_utility=(
                        float(output.base_utilities[candidate_index])
                        if output is not None
                        else None
                    ),
                    context_effect=(
                        float(output.context_effects[candidate_index])
                        if output is not None
                        else None
                    ),
                    confidence=confidence.level,
                    confidence_score=round(confidence.score, 4),
                    wait_minutes=round(
                        (now - candidate.patient.arrival_time).total_seconds() / 60,
                        2,
                    ),
                    state=state,
                    reasons=list(dict.fromkeys(reasons + list(confidence.reasons))),
                    alerts=list(dict.fromkeys(alerts)),
                    missing_information=list(candidate.features.missing_information),
                    triggered_rules=candidate.safety.rule_ids,
                    recommended_action=action,
                    is_stale=not model_available,
                )
            )

        snapshot = QueueSnapshot(
            generated_at=now,
            mode=queue_mode,
            model_status="ready" if model_available else "fallback",
            model_version=self.cdm.version,
            patient_count=len(entries),
            queue_pressure=round(pressure, 3),
            entries=entries,
            warnings=warnings,
        )
        if model_available:
            with self._lock:
                self._last_good_positions = {
                    entry.patient_id: entry.position for entry in entries
                }
        return snapshot
