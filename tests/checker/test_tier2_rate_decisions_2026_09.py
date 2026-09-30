"""The four rules the two-tier round left over the Tier 2 rate, decided.

Round: 2026-09-18. Spec:
docs/superpowers/specs/2026-09-18-four-rules-over-the-tier-2-rate.md

BS-006 was tightened (94 firings to 7, 20.0 per 10k to 1.5). flagged_term,
rule_of_three_density and BS-009 were read and deliberately left alone, with
the reasons written into data/caveats.json. This file pins the tightening and
the three recorded decisions, so a later round starts from the numbers instead
of rediscovering them.
"""

import json
import pathlib

import pytest

from src.checker.loader import load_regex_structures
from src.checker.structures import find_regex_structures
from tests.support.fp_corpus import (
    assert_tier1_clear,
    rate_per_10k,
    tier2_available,
    tier2_sweep,
)

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"


def bs006(text: str) -> list[dict]:
    rules = [s for s in load_regex_structures() if s["id"] == "BS-006"]
    assert rules, "BS-006 is missing from banned_structures.json"
    return find_regex_structures(text, rules)


def bs011(text: str) -> list[dict]:
    """Must-be-zero control: the pattern narrowed in the previous round."""
    rules = [s for s in load_regex_structures() if s["id"] == "BS-011"]
    return find_regex_structures(text, rules)


# The attested tell. AP-006 is the first of them.
TELLS = [
    "This approach is not just efficient, but also scalable across teams.",
    "It is not just a tool, but a platform.",
    "The result is not only faster but also cheaper.",
    "The rebuild was not just a refresh but a rethink of the whole system.",
]

# The ordinary correlative, verbatim from Tier 2, which the deployed pattern
# flagged and the tightened one declines.
HUMAN_CORRELATIVE = [
    "I was not only instructed in everything that was taught at Greenleaf, "
    "but was soon engaged in helping.",
    "The room was not only very untidy but very dirty.",
    "Mr. and Mrs. Snagsby are not only one bone and one flesh, "
    "but, to the neighbours' thinking, one voice too.",
]

# The recall step given up on purpose: the bare correlative used as a flourish.
# Carried by the self_review antithesis item and the sibling prompt instead.
NARROWED_AWAY = "This is not only a design problem but a cultural one."


@pytest.mark.parametrize("text", TELLS)
def test_the_tell_still_fires(text):
    assert bs006(text), text


@pytest.mark.parametrize("text", HUMAN_CORRELATIVE)
def test_the_ordinary_correlative_is_declined(text):
    assert not bs006(text), text


def test_the_bare_correlative_flourish_is_no_longer_mechanized():
    assert not bs006(NARROWED_AWAY)


def test_tier1_stays_clear_of_bs006():
    assert_tier1_clear(bs006, "BS-006")


@pytest.mark.skipif(not tier2_available(), reason="Tier 2 corpus absent; python -m eval.fpcorpus.fetch_longform")
def test_bs006_is_inside_the_tier2_bar_with_controls_in_the_same_run():
    total, rate, per_work = tier2_sweep(bs006)
    assert total == 7, per_work
    assert rate == pytest.approx(1.5, abs=0.05), rate
    assert rate <= 5.0
    # Discriminating controls, same run: one rule that must be zero, and the
    # count the tightening started from, recomputed rather than quoted.
    zero_total, _, _ = tier2_sweep(bs011)
    assert zero_total == 0
    assert rate_per_10k(94) == pytest.approx(20.0, abs=0.05)


def test_bs006_entry_records_the_narrowing():
    entry = next(
        s
        for s in json.loads((DATA / "banned_structures.json").read_text())["structures"]
        if s["id"] == "BS-006"
    )
    assert "but also" in entry["detection"]["pattern"]
    assert entry["gate"] == "checklist"
    assert "20.0 per 10k" in entry["description"]


def _caveat(caveat_id: str) -> dict:
    caveats = json.loads((DATA / "caveats.json").read_text())["core_caveats"]
    return {c["id"]: c for c in caveats}[caveat_id]


def test_lexicon_decision_is_recorded_with_its_numbers():
    explanation = _caveat("lexicon_rate_is_not_a_detector_rate")["explanation"]
    for number in ("164", "34.8", "0.29", "10 times on the calibration corpus"):
        assert number in explanation, number


def test_rule_of_three_decision_is_recorded_with_its_numbers():
    explanation = _caveat("rhetorical_figures_defeat_shape_detection")["explanation"]
    assert "97" in explanation and "20.6 per 10k" in explanation
    # The anaphora round's numbers must survive the append.
    assert "0/15" in explanation and "5.7 per 10k" in explanation
