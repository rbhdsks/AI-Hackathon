from __future__ import annotations

import numpy as np
import pytest

from patient_triage.models.cdm import FeatureContextDependentModel
from patient_triage.models.features import FEATURE_NAMES


def test_empty_choice_set():
    output = FeatureContextDependentModel().score(np.empty((0, len(FEATURE_NAMES))))
    assert output.utilities.size == 0
    assert output.probabilities.size == 0


def test_single_patient_has_no_context_and_probability_one():
    output = FeatureContextDependentModel().score(np.ones((1, len(FEATURE_NAMES))))
    assert output.context_effects.tolist() == [0.0]
    assert output.probabilities.tolist() == [1.0]


def test_probabilities_sum_to_one_and_are_finite():
    matrix = np.asarray(
        [[0.2, 0.8, 0.4, 0.1, 0, 0.2, 0], [0.5, 0.4, 0.2, 0.9, 0.7, 0.1, 1.0]]
    )
    output = FeatureContextDependentModel().score(matrix)
    assert np.isfinite(output.probabilities).all()
    assert output.probabilities.sum() == pytest.approx(1.0)
    assert (output.probabilities > 0).all()


def test_identical_patients_have_equal_probability():
    output = FeatureContextDependentModel().score(np.ones((4, len(FEATURE_NAMES))))
    assert output.probabilities == pytest.approx(np.full(4, 0.25))


def test_context_effect_changes_when_waiting_set_changes():
    model = FeatureContextDependentModel()
    first = np.asarray([0.2, 0.4, 0.2, 0.8, 0.1, 0.2, 0.0])
    second = np.asarray([0.5, 0.7, 0.4, 0.1, 0.0, 0.1, 0.6])
    third = np.asarray([0.9, 0.9, 0.8, 1.0, 0.8, 0.9, 1.0])
    two = model.score(np.vstack([first, second]))
    three = model.score(np.vstack([first, second, third]))
    assert two.base_utilities[0] == pytest.approx(three.base_utilities[0])
    assert two.context_effects[0] != pytest.approx(three.context_effects[0])


@pytest.mark.parametrize(
    "bad",
    [np.zeros(7), np.zeros((2, 6)), np.zeros((2, 8))],
)
def test_wrong_shape_rejected(bad):
    with pytest.raises(ValueError, match="shape"):
        FeatureContextDependentModel().score(bad)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_non_finite_features_rejected(value):
    matrix = np.zeros((2, len(FEATURE_NAMES)))
    matrix[0, 0] = value
    with pytest.raises(ValueError, match="finite"):
        FeatureContextDependentModel().score(matrix)


def test_softmax_is_stable_for_large_finite_values():
    matrix = np.full((3, len(FEATURE_NAMES)), 1e100)
    output = FeatureContextDependentModel().score(matrix)
    assert np.isfinite(output.probabilities).all()
    assert output.probabilities.sum() == pytest.approx(1.0)


def test_model_is_deterministic():
    matrix = np.arange(21, dtype=float).reshape(3, 7) / 21
    model = FeatureContextDependentModel()
    assert model.score(matrix).utilities == pytest.approx(model.score(matrix).utilities)
