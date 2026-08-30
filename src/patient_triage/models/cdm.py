"""Feature-conditioned Context-Dependent Model (CDM) for patient ranking."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from patient_triage.models.features import FEATURE_NAMES


@dataclass(frozen=True, slots=True)
class CDMOutput:
    """Store the different outputs produced by the CDM.

    Each array contains one value for every patient in the waiting set.
    """

    # Score calculated using only the patient's own features.
    base_utilities: np.ndarray

    # Additional score caused by interaction with other waiting patients.
    context_effects: np.ndarray

    # Final score: base utility + context effect.
    utilities: np.ndarray

    # Softmax-normalized probability for each patient.
    probabilities: np.ndarray


class FeatureContextDependentModel:
    """Rank patients using their own condition and the current queue context.

    For patient ``i`` with feature vector ``x_i`` and waiting set ``S``:

        U_i(S) = beta^T x_i + mean_{j != i}(x_i^T W x_j)

    In simple terms:

        final score = patient's own urgency + waiting-room context

    The softmax function converts the final scores into probabilities.

    Safety rules are handled outside this model. Therefore, this statistical
    model cannot override a critical escalation produced by a safety rule.
    """

    def __init__(self, version: str = "feature-cdm-v1") -> None:
        """Initialize the CDM parameters.

        Important:
            These coefficients are transparent prototype values. They are not
            clinically trained or validated and must not be used for real
            patient care without proper clinical validation.
        """

        # Version name is stored in audit records so that every recommendation
        # can be linked to the model version that produced it.
        self.version = version

        # Common starting value added to every patient's base utility.
        self.intercept = -0.1

        # Importance assigned to each feature in FEATURE_NAMES.
        #
        # The order of these values must exactly match the order in
        # FEATURE_NAMES. A larger positive value means that the feature has
        # a stronger effect on the patient's base urgency score.
        self.beta = np.asarray(
            [2.4, 2.1, 0.4, 0.65, 1.5, 0.45, 0.3],
            dtype=np.float64,
        )

        # W is the context-interaction matrix from the CDM formula.
        #
        # Rows represent features of the patient being scored.
        # Columns represent average features of the other waiting patients.
        #
        # Initially, every interaction is zero. We then add only the
        # interactions that the prototype is designed to consider.
        self.interactions = np.zeros(
            (len(FEATURE_NAMES), len(FEATURE_NAMES)),
            dtype=np.float64,
        )

        # Convert feature names into their numerical column positions.
        #
        # Example:
        #     index["waiting"] gives the column containing waiting-time risk.
        index = {
            name: position
            for position, name in enumerate(FEATURE_NAMES)
        }

        # Patient's physiology risk interacting with the average physiology
        # risk of the other patients.
        self.interactions[
            index["physiology_risk"],
            index["physiology_risk"],
        ] = 0.25

        # Patient's physiology risk interacting with how long other patients
        # have been waiting.
        self.interactions[
            index["physiology_risk"],
            index["waiting"],
        ] = 0.2

        # Patient's symptom risk interacting with the average physiology risk
        # in the waiting room.
        self.interactions[
            index["symptom_risk"],
            index["physiology_risk"],
        ] = 0.15

        # Patient's waiting-time risk interacting with the average waiting-time
        # risk of the rest of the queue.
        self.interactions[
            index["waiting"],
            index["waiting"],
        ] = 0.9

        # Patient deterioration interacting with the average physiology risk
        # of the other waiting patients.
        self.interactions[
            index["deterioration"],
            index["physiology_risk"],
        ] = 0.8

        # Patient uncertainty interacting with the average physiology risk of
        # the other patients.
        self.interactions[
            index["uncertainty"],
            index["physiology_risk"],
        ] = 0.7

        # Patient vulnerability interacting with the average symptom risk in
        # the waiting room.
        self.interactions[
            index["vulnerability"],
            index["symptom_risk"],
        ] = 0.4

    def score(self, feature_matrix: np.ndarray) -> CDMOutput:
        """Calculate CDM scores and probabilities for the current waiting set.

        Args:
            feature_matrix:
                A two-dimensional matrix where every row represents one
                patient and every column represents one feature.

                Expected shape:

                    (number_of_patients, number_of_features)

        Returns:
            CDMOutput containing the base scores, context effects, final
            utilities, and probabilities.
        """

        # Convert the supplied data into a NumPy float matrix so that all
        # mathematical operations use a consistent numeric type.
        matrix = np.asarray(feature_matrix, dtype=np.float64)

        # The input must be two-dimensional and must contain exactly one column
        # for every feature listed in FEATURE_NAMES.
        if matrix.ndim != 2 or matrix.shape[1] != len(FEATURE_NAMES):
            raise ValueError(
                f"feature matrix must have shape (n, {len(FEATURE_NAMES)})"
            )

        # Reject NaN and infinite values because they would make the model
        # scores and probabilities invalid.
        if not np.isfinite(matrix).all():
            raise ValueError(
                "feature matrix must contain only finite values"
            )

        # Number of patients currently present in the waiting set.
        patient_count = matrix.shape[0]

        # If the waiting set is empty, return four empty arrays.
        if patient_count == 0:
            empty = np.empty(0, dtype=np.float64)

            return CDMOutput(
                base_utilities=empty,
                context_effects=empty.copy(),
                utilities=empty.copy(),
                probabilities=empty.copy(),
            )

        # Calculate each patient's score using only their own features:
        #
        #     base_i = intercept + beta^T x_i
        #
        # "matrix @ self.beta" calculates this for every patient at once.
        base = self.intercept + matrix @ self.beta

        # Context requires at least one other patient.
        if patient_count == 1:
            # When only one patient is waiting, there is nobody else with whom
            # the patient can interact. Therefore, the context effect is zero.
            context_effects = np.zeros(1, dtype=np.float64)

        else:
            # Calculate the average feature vector of all OTHER patients.
            #
            # For each patient:
            #   1. Add the features of everyone in the queue.
            #   2. Subtract the current patient's own features.
            #   3. Divide by the number of remaining patients.
            context_means = (
                matrix.sum(axis=0) - matrix
            ) / (patient_count - 1)

            # Calculate one context effect for every patient:
            #
            #     context_i = x_i^T W average(x_j)
            #
            # This einsum expression is a vectorized equivalent of:
            #
            #     context_effects[i] = (
            #         matrix[i]
            #         @ self.interactions
            #         @ context_means[i]
            #     )
            context_effects = np.einsum(
                "ij,jk,ik->i",
                matrix,
                self.interactions,
                context_means,
            )

        # Combine the patient's individual score and contextual score:
        #
        #     final utility = base utility + context effect
        utilities = base + context_effects

        # Apply a numerically stable softmax.
        #
        # Subtracting the maximum does not change the final probabilities, but
        # it prevents very large exponential values from causing overflow.
        shifted = utilities - utilities.max()
        exponentials = np.exp(shifted)

        # Convert utilities into probabilities that sum to one.
        probabilities = exponentials / exponentials.sum()

        return CDMOutput(
            base_utilities=base,
            context_effects=context_effects,
            utilities=utilities,
            probabilities=probabilities,
        )