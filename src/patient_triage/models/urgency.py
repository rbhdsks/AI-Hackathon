"""Transparent patient-level urgency score used before contextual ranking."""

from __future__ import annotations

import numpy as np

from patient_triage.domain.enums import AcuityLevel
from patient_triage.models.features import FEATURE_NAMES, FeatureVector


class TransparentUrgencyModel:
    """Fixed illustrative coefficients, intentionally inspectable by judges."""

    def __init__(self) -> None:
        self.intercept = -0.2
        self.coefficients = np.asarray(
            [2.8, 2.4, 0.5, 0.8, 1.8, 0.65, 0.45], dtype=np.float64
        )

    def score(self, features: FeatureVector) -> float:
        if features.values.shape != (len(FEATURE_NAMES),):
            raise ValueError("unexpected feature dimension")
        return float(self.intercept + features.values @ self.coefficients)

    @staticmethod
    def classify(score: float) -> AcuityLevel:
        if not np.isfinite(score):
            raise ValueError("urgency score must be finite")
        # Thresholds intentionally favour escalation in this synthetic safety
        # demonstration. False-negative cost is treated as higher than the
        # operational cost of an unnecessary review.
        if score >= 4.5:
            return AcuityLevel.EMERGENT
        if score >= 1.4:
            return AcuityLevel.URGENT
        if score >= 0.65:
            return AcuityLevel.LESS_URGENT
        return AcuityLevel.NON_URGENT
