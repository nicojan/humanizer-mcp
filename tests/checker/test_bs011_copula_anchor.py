"""BS-011 is copula-anchored, and its remaining false positive is accepted on purpose.

Round: 2026-09-18. Spec:
docs/superpowers/specs/2026-09-18-bs011-copula-anchor-and-the-modern-prose-hole.md

The deployed two-token pattern fired 358 times on 47,088 sentences of pre-1930
prose, 76.0 per 10k, the worst rate of any rule in the server, and declined 1
of 6 constructed hard negatives. The copula anchor scores 0 on that corpus with
the same 6/6 recall on the attested tells and 6/6 on the hard negatives.

The part that is NOT clean, and is shipped knowingly: on a modern control of
2,692 sentences (this repo's docs plus the sibling PROMPT.md) it fires 9 times,
33.4 per 10k, and 8 of those 9 are scope notes rather than tells. The attested
tell and the scope note are the same construction, so no narrowing separates
them. ACCEPTED_FALSE_POSITIVES below pins those firings as expected behaviour.
A later round that narrows the rule has to break those tests deliberately and
say why in caveats.contrastive_scope_notes_are_the_same_shape.
"""

import json
import pathlib
import time

import pytest

from src.checker.loader import load_regex_structures, load_self_review
from src.checker.structures import find_regex_structures
from tests.support.fp_corpus import (
    TIER2_SENTENCES,
    assert_tier1_clear,
    tier2_available,
    tier2_sweep,
)

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"


def bs011(text: str) -> list[dict]:
    rules = [s for s in load_regex_structures() if s["id"] == "BS-011"]
    assert rules, "BS-011 is missing from banned_structures.json"
    return find_regex_structures(text, rules)


def bs006(text: str) -> list[dict]:
    """Discriminating control: a different deployed regex that still fires on
    long-form human prose. Without it, a BS-011 zero and a broken sweep are the
    same output. BS-006 was itself narrowed later the same day, from 20.0 per
    10k to 1.5, so this control asserts that it fires rather than how often."""
    rules = [s for s in load_regex_structures() if s["id"] == "BS-006"]
    return find_regex_structures(text, rules)


# The attested tell, copula plus noun plus a Y that closes the clause.
ATTESTED_TELLS = [
    "The work is judgement, not process.",
    "It is a discipline, not a talent.",
    "The answer is restraint, not addition.",
    "This is a craft, not a formula.",
    "Design is clarity, not decoration.",
    "The point is trust, not speed.",
]

# Ordinary human negation. Five are verbatim from the Tier 2 corpus, where the
# deployed pattern flagged all of them.
HARD_NEGATIVES = [
    "He was very young, not more than nineteen then.",
    "He spoke with Richard Carstone, not seated, but standing.",
    "There is another suit in Chancery, not yet decided, which was commenced.",
    "I was not only instructed in everything, but was soon engaged in helping.",
    "They were one man, not thirty.",
    "That is the captain's work, not mine.",
]

# The accepted cost, measured on the modern control. Every one of these is a
# scope note fixing the referent of a rule just stated, and every one fires.
# gate=checklist, so the cost is one justification per firing.
ACCEPTED_FALSE_POSITIVES = [
    "The tell is the appending, not the phrase.",
    "The unit is the collocation, not the word.",
    "The self-review rubric is data, not code.",
    "A repeated shape is judgment, not a detector.",
    "Two firings in one section are a finding, not noise.",
    "An unparseable line is dropped, not guessed.",
    "The response was 406, not 421.",
    "The winner is Maria, not Tom.",
]

# Contrastive tells outside the copula frame. The narrowing gives these up on
# purpose; they are carried by the self_review rubric item instead. AP-005's
# own before-text is the first of them, which is the cost stated plainly.
NARROWED_AWAY = [
    "The brush-stroke wordmark comes from paint on paper, not the polished apps she gave up on.",
    "We chose depth, not breadth.",
    "The aim is speed, not polish, and that shapes every decision.",
    "Good design rewards patience, not speed.",
]


@pytest.mark.parametrize("text", ATTESTED_TELLS)
def test_attested_tells_still_fire(text):
    assert bs011(text), text


@pytest.mark.parametrize("text", HARD_NEGATIVES)
def test_human_negation_is_declined(text):
    assert not bs011(text), text


@pytest.mark.parametrize("text", ACCEPTED_FALSE_POSITIVES)
def test_scope_notes_fire_and_that_is_the_accepted_cost(text):
    """Documented, not desired. See the module docstring before 'fixing' this."""
    assert bs011(text), text


@pytest.mark.parametrize("text", NARROWED_AWAY)
def test_non_copula_contrastive_is_no_longer_mechanized(text):
    """Negative regression: recall the round gave up, pinned so a later widening
    is a decision rather than an accident."""
    assert not bs011(text), text


def test_tier1_is_clear_of_bs011():
    """The standing BS-011 firing on the calibration corpus is gone with it."""
    assert_tier1_clear(bs011, "BS-011")


def test_tier1_control_still_fires():
    """Same run, discriminating control: the sweep can still find something."""
    assert bs006("This approach is not just efficient, but also scalable.")


@pytest.mark.skipif(not tier2_available(), reason="Tier 2 corpus absent; python -m eval.fpcorpus.fetch_longform")
def test_tier2_rate_is_zero_with_a_control_in_the_same_run():
    total, rate, per_work = tier2_sweep(bs011)
    control_total, control_rate, _ = tier2_sweep(bs006)
    assert control_total > 0, "control did not fire; the sweep is broken, not clean"
    assert total == 0, per_work
    assert rate == 0.0
    assert control_rate > 0.0, control_total
    assert TIER2_SENTENCES == 47088


def test_pattern_is_redos_safe():
    start = time.perf_counter()
    bs011("word, not " * 20000)
    assert time.perf_counter() - start < 1.0


def test_entry_keeps_its_gate_and_records_the_accepted_false_positive():
    entry = next(
        s
        for s in json.loads((DATA / "banned_structures.json").read_text())["structures"]
        if s["id"] == "BS-011"
    )
    assert entry["gate"] == "checklist"
    assert entry["detection"]["confidence"] == "low"
    assert "is|was|are|were" in entry["detection"]["pattern"]
    assert "scope" in entry["description"].lower()


def test_self_review_carries_the_narrowed_away_frame():
    items = load_self_review()
    matches = [i for i in items if "X, not Y" in i]
    assert len(matches) == 1, items
    assert "BS-011" in matches[0]


def test_caveats_record_the_measurement():
    caveats = json.loads((DATA / "caveats.json").read_text())["core_caveats"]
    by_id = {c["id"]: c for c in caveats}
    assert "contrastive_scope_notes_are_the_same_shape" in by_id
    explanation = by_id["contrastive_scope_notes_are_the_same_shape"]["explanation"]
    for number in ("358", "76.0", "1/9", "2,692", "33.4"):
        assert number in explanation, number
