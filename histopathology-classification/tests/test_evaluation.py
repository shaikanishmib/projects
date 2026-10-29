import numpy as np
import pytest

from histopathology.data import Sample
from histopathology.evaluation import evaluate, metrics


def test_known_confusion_and_threshold():
    result = metrics(np.array([0, 0, 1, 1]), np.array([.1, .5, .4, .9]))
    assert result["confusion_matrix"] == [[1, 1], [1, 1]]
    assert result["balanced_accuracy"] == .5
    assert result["sensitivity"] == .5
    assert result["specificity"] == .5


def test_patient_aggregation_does_not_count_tiles_as_patients():
    samples = [Sample("a", "p0", "a.png", 0, "x"), Sample("b", "p0", "b.png", 0, "y"),
               Sample("c", "p1", "c.png", 1, "z")]
    result = evaluate(samples, np.array([.9, .0, .8]), seed=4, bootstrap=100)
    assert result["image"]["n"] == 3
    assert result["patient"]["n"] == 2
    assert result["patient"]["confusion_matrix"] == [[1, 0], [0, 1]]
    assert [row["image_id"] for row in result["errors"]] == ["a"]
    assert result == evaluate(samples, np.array([.9, .0, .8]), seed=4, bootstrap=100)


@pytest.mark.parametrize("probabilities", [[float("nan"), .2], [-.1, .2], [1.1, .2], [.2]])
def test_bad_predictions_rejected(probabilities):
    with pytest.raises(ValueError):
        metrics(np.array([0, 1]), np.array(probabilities))


def test_single_class_auc_is_explicitly_undefined():
    result = metrics(np.array([0, 0]), np.array([.1, .2]))
    assert result["roc_auc"] is None
    assert result["sensitivity"] is None
