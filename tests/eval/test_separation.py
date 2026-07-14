import pytest

from eval.separation import roc_auc, separation_verdict


def test_auc_perfect_separation():
    assert roc_auc([5, 4, 4], [1, 2]) == 1.0


def test_auc_no_separation_is_half():
    assert roc_auc([3], [3]) == 0.5


def test_auc_inverted_is_zero():
    assert roc_auc([1], [5]) == 0.0


def test_auc_empty_raises():
    with pytest.raises(ValueError):
        roc_auc([], [1])


def test_verdict_passes_above_bar():
    v = separation_verdict([5, 5, 4], [1, 2, 2], min_auc=0.75)
    assert v["passed"] is True
    assert v["auc"] == 1.0
    assert v["human_mean"] > v["ai_mean"]
    assert v["n_human"] == 3 and v["n_ai"] == 3


def test_verdict_fails_below_bar():
    v = separation_verdict([3, 2], [3, 2], min_auc=0.75)
    assert v["passed"] is False
    assert v["auc"] == 0.5
