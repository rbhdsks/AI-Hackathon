"""Feature-conditioned context-dependent choice model (CDM)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from patient_triage.models.features import FEATURE_NAMES


@dataclass(frozen=True, slots=True)
class CDMOutput:
    base_utilities: np.ndarray
    context_effects: np.ndarray
    utilities: np.ndarray
    probabilities: np.ndarray


class FeatureContextDependentModel:
    """Rank dynamic patients using feature-level context interactions.

    For patient feature vector ``x_i`` and current waiting set ``S``:

        U_i(S) = beta^T x_i + mean_{j != i}(x_i^T W x_j)

    Choice probabilities are the softmax of these utilities. Safety rules are
    intentionally outside this model and are applied as hard ordering floors.
    """

    def __init__(self, version: str = "feature-cdm-v1") -> None:
        self.version = version
        self.intercept = -0.1
        self.beta = np.asarray([2.4, 2.1, 0.4, 0.65, 1.5, 0.45, 0.3], dtype=np.float64)
        self.interactions = np.zeros((len(FEATURE_NAMES), len(FEATURE_NAMES)))
        index = {name: position for position, name in enumerate(FEATURE_NAMES)}
        self.interactions[index["physiology_risk"], index["physiology_risk"]] = 0.25
        self.interactions[index["physiology_risk"], index["waiting"]] = 0.2
        self.interactions[index["symptom_risk"], index["physiology_risk"]] = 0.15
        self.interactions[index["waiting"], index["waiting"]] = 0.9
        self.interactions[index["deterioration"], index["physiology_risk"]] = 0.8
        self.interactions[index["uncertainty"], index["physiology_risk"]] = 0.7
        self.interactions[index["vulnerability"], index["symptom_risk"]] = 0.4

    def score(self, feature_matrix: np.ndarray) -> CDMOutput:
        matrix = np.asarray(feature_matrix, dtype=np.float64)
        if matrix.ndim != 2 or matrix.shape[1] != len(FEATURE_NAMES):
            raise ValueError(
                f"feature matrix must have shape (n, {len(FEATURE_NAMES)})"
            )
        if not np.isfinite(matrix).all():
            raise ValueError("feature matrix must contain only finite values")

        patient_count = matrix.shape[0]
        if patient_count == 0:
            empty = np.empty(0, dtype=np.float64)
            return CDMOutput(empty, empty.copy(), empty.copy(), empty.copy())

        base = self.intercept + matrix @ self.beta
        if patient_count == 1:
            context_effects = np.zeros(1, dtype=np.float64)
        else:
            context_means = (matrix.sum(axis=0) - matrix) / (patient_count - 1)
            context_effects = np.einsum(
                "ij,jk,ik->i", matrix, self.interactions, context_means
            )

        utilities = base + context_effects
        shifted = utilities - utilities.max()
        exponentials = np.exp(shifted)
        probabilities = exponentials / exponentials.sum()
        return CDMOutput(base, context_effects, utilities, probabilities)
