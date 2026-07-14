from pathlib import Path

import pytest

from eval.reference import (
    AI_DIR,
    HUMAN_DIR,
    move_verdict,
    pile_reference,
    z_to_human,
)

_needs_corpus = pytest.mark.skipif(
    not any(Path(HUMAN_DIR).glob("*.txt")),
    reason="human calibration corpus is not redistributed (copyrighted excerpts); "
    "see eval/corpus/SOURCES.md to reconstruct it from the archived source URLs",
)


def test_pile_reference_computes_stats(tmp_path):
    (tmp_path / "a.txt").write_text("alpha beta gamma delta epsilon", encoding="utf-8")
    (tmp_path / "b.txt").write_text("one two three four five six", encoding="utf-8")
    ref = pile_reference(["hapax_ratio"], tmp_path)
    f = ref["hapax_ratio"]
    assert f["n"] == 2
    assert f["lo"] <= f["mean"] <= f["hi"]
    assert f["sd"] >= 0.0


def test_pile_reference_empty_is_safe(tmp_path):
    assert pile_reference(["hapax_ratio"], tmp_path) == {}


def test_z_to_human_is_signed_distance_in_sd_units():
    feat = {"mean": 0.75, "sd": 0.05, "lo": 0.6, "hi": 0.9, "n": 16}
    assert z_to_human(0.75, feat) == 0.0
    assert z_to_human(0.80, feat) == 1.0
    assert z_to_human(0.70, feat) == -1.0


def test_z_to_human_handles_zero_sd():
    assert z_to_human(0.9, {"mean": 0.75, "sd": 0.0}) == 0.0


def test_move_verdict_toward_and_away():
    human = {"mean": 0.75, "sd": 0.05, "lo": 0.6, "hi": 0.9, "n": 16}
    # Both above the mean; loop is farther from it -> away (the case the
    # original grid mislabelled as "texture improves").
    assert move_verdict(0.80, 0.86, human) == "away_from_human"
    # Loop closer to the mean -> toward.
    assert move_verdict(0.86, 0.78, human) == "toward_human"
    # No change -> flat.
    assert move_verdict(0.80, 0.80, human) == "flat"


@_needs_corpus
def test_corpus_hapax_direction_is_ai_higher():
    """Pins the load-bearing fact behind the 2026-06-29 correction: in the
    calibration corpus, AI text scores HIGHER on hapax than human text, so a
    rising hapax is a move toward the AI side, not toward human. If a future
    corpus change flips this, the grid's verdict logic must be revisited."""
    human = pile_reference(["hapax_ratio", "mattr"], HUMAN_DIR)
    ai = pile_reference(["hapax_ratio", "mattr"], AI_DIR)
    assert human and ai, "calibration corpus must be present"
    assert human["hapax_ratio"]["mean"] < ai["hapax_ratio"]["mean"]
    assert human["mattr"]["mean"] < ai["mattr"]["mean"]
