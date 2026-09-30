"""Anaphora abuse is a recorded NEGATIVE, not a gap waiting to be filled.

Three or more consecutive sentences opening on the same word is an attested
model tell, and it is deliberately NOT mechanized beyond the existing BS-009
This/These/It chain. Spec:
docs/superpowers/specs/2026-09-18-anaphora-abuse-negative-result.md

The reason is that the abusive case and the rhetorical figure are the same
construction. Probed against 47,088 sentences of pre-1930 public-domain prose
(Project Gutenberg ids 1023, 1342, 2701, 205, 74, 1661), the loosest
formulation scored 75.4 false positives per 10k sentences and the best - same
first two tokens, threshold three, every sentence at most ten words - scored
3.2 per 10k with all fifteen firings read and found legitimate, i.e. 0/15
precision. Raising the threshold to four scored 0/6 recall against the attested
three-sentence tell while still firing on human prose.

Two of the passages below are Thoreau and Melville. They are the point: they
carry every property a detector can read that the attested tell carries. If a
later round makes these fail, it has reintroduced a rule that flags Walden, and
it needs to revisit the design doc and caveats.rhetorical_figures_defeat_shape_detection
first.

The tell is carried by the self_review rubric instead (the anaphora item), and
that item's presence is pinned here too.
"""

import json
import pathlib

import pytest

from src.checker.loader import load_regex_structures, load_self_review
from src.checker.structures import (
    find_heuristic_structures,
    find_regex_structures,
    find_rule_of_three_density,
)

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"

# Deliberate human anaphora. Every one of these fired on at least one candidate
# formulation during the probe; none is a defect. The Thoreau passage is NOT in
# this list: it opens on "It" and so is already flagged by BS-009 today, which
# is a measured pre-existing false positive, pinned separately below.
HUMAN_ANAPHORA = [
    # Melville, Moby-Dick.
    "Forty years of continual whaling! Forty years of privation, and peril, and storm-time! "
    "Forty years on the pitiless sea!",
    # Dickens, Bleak House.
    "As my father's came there. As my brother's. As my sister's. As my own.",
    # Doyle, Sherlock Holmes.
    "In the dress is a pocket. In the pocket is a card-case. In the card-case is a note.",
    # Dickens, Bleak House - the shop-inscription catalogue, five limbs.
    "In another was the inscription BONES BOUGHT. In another, KITCHEN-STUFF BOUGHT. "
    "In another, OLD IRON BOUGHT. In another, WASTE-PAPER BOUGHT.",
    # Ordinary paragraph construction, the FP class the previous round predicted.
    "The platform handles scheduling. The database stores the roster. "
    "The worker sends the reminders.",
]

# The attested model tell. It is NOT expected to be flagged - that is the whole
# finding. Pinned so a later round cannot quietly start matching it without
# also making the Thoreau cases fail and forcing a re-read of the spec.
ATTESTED_TELL = [
    "They assume users will pay. They assume the market is ready. They assume nothing changes.",
    "We believe in craft. We believe in speed. We believe in shipping.",
    "The platform scales. The platform adapts. The platform endures.",
]

# BS-009 covers the This/These/It chain, and it does not distinguish the model
# tell from the figure inside that narrow slice either. Both of these are
# flagged today. Kept as-is (gate=checklist, and the rule predates every round
# since 2026-06), but pinned so the cost is visible and measured rather than
# assumed away. See caveats.rhetorical_figures_defeat_shape_detection.
BS009_FLAGS_BOTH = [
    # Thoreau, Walden - deliberate anaphora, flagged.
    "It does not keep the country free. It does not settle the West. It does not educate.",
    # The attested model tell in the same shape - also flagged.
    "It reflects the brief. It reflects the budget. It reflects the deadline.",
]


def _all_structure_findings(text: str) -> list[dict]:
    """Every structural detector, the way the full sweep runs them."""
    return (
        find_regex_structures(text, load_regex_structures())
        + find_heuristic_structures(text)
        + find_rule_of_three_density(text)
    )


@pytest.mark.parametrize("text", HUMAN_ANAPHORA)
def test_deliberate_human_anaphora_is_not_flagged(text):
    """A rule that flags Walden is a rule that flattens good writing."""
    assert not _all_structure_findings(text), text


@pytest.mark.parametrize("text", ATTESTED_TELL)
def test_attested_anaphora_tell_stays_unmechanized(text):
    """Negative regression: the tell is a rubric item, not a detector.

    BS-009 covers the This/These/It chain only, at a threshold of three, and
    none of these three open on This/These/It in a way that chains.
    """
    assert not _all_structure_findings(text), text


@pytest.mark.parametrize("text", BS009_FLAGS_BOTH)
def test_bs009_flags_the_figure_and_the_tell_alike(text):
    """The narrow slice that IS mechanized cannot tell them apart either.

    This is the evidence for the negative, not a bug to fix: inside the
    This/These/It chain, Thoreau and the model tell both fire. Widening the
    opener set to the whole language would multiply this.
    """
    hits = _all_structure_findings(text)
    assert any(f["id"] == "BS-009" for f in hits), text


def test_bs009_still_covers_the_this_chain_it_was_written_for():
    """Discriminating control: the sweep is not simply returning nothing.

    Without this, every assertion above would pass on a broken import.
    """
    hits = _all_structure_findings(
        "This shows the pattern. This confirms the trend. This settles the question."
    )
    assert any(f["id"] == "BS-009" for f in hits), hits


def test_self_review_carries_the_anaphora_item():
    items = load_self_review()
    matches = [i for i in items if "Anaphora" in i]
    assert len(matches) == 1, items
    item = matches[0]
    # The definitional caveat must stay attached to the check: the form is
    # legitimate, and the tell is purposeless repetition.
    assert "Thoreau" in item
    assert "BS-009" in item


def test_caveats_record_the_negative_and_the_corpus_limitation():
    caveats = json.loads((DATA / "caveats.json").read_text())["core_caveats"]
    ids = {c["id"] for c in caveats}
    assert "rhetorical_figures_defeat_shape_detection" in ids
    assert "short_corpus_cannot_validate_run_detectors" in ids
    by_id = {c["id"]: c for c in caveats}
    # The measured numbers are the load-bearing part - they are what stops a
    # later round re-litigating this from intuition.
    assert "0/15" in by_id["rhetorical_figures_defeat_shape_detection"]["explanation"]
    assert "5.7 per 10k" in by_id["rhetorical_figures_defeat_shape_detection"]["explanation"]
    short = by_id["short_corpus_cannot_validate_run_detectors"]
    assert "109 sentences" in short["explanation"]
    assert "75.4" in short["explanation"]
