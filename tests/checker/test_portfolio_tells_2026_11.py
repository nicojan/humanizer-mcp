"""The portfolio-copy round: three self-review items, two rubric extensions, an
anti-pattern and a caveat, from lines a human editor flagged as "AI-coded" on
nicojan.com. No regex rule shipped.

Round: 2026-11-09. Spec:
docs/superpowers/specs/2026-11-09-portfolio-copy-tells.md

Between 2026-10-11 and 2026-11-05 the site's owner flagged 31 lines of
Claude-written portfolio copy. All 31 passed the checker. Five shapes were
probed as regex rules. The strongest, the verbless numeral-contrast caption
("One count, four moments"), measured zero on Tier 1, Tier 2, pre-2022 essays
and pre-2022 Wikipedia against a control that fired, and was then rejected: an
adversarial review found about 100 legitimate terse lines with the same shape
(dosing, box scores, listings, headlines). This file pins what shipped, and
keeps those lines as a standing hard-negative set for every structural rule.
"""

import json
import pathlib

import pytest

from src.checker import run_checks
from src.checker.loader import load_regex_structures, load_self_review

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"

# Ordinary terse writing in the numeral-contrast shape, from the round's
# adversarial review. The rejected caption rule flagged every one of these.
TERSE_REGISTER = [
    "Two tablets, every four hours.",
    "One tablet, three times daily.",
    "Two drops, each nostril.",
    "Two eggs, all beaten.",
    "One coffee, no sugar.",
    "Two lattes, one with oat milk.",
    "Three bedrooms, one bath.",
    "One owner, no accidents.",
    "Two queens, one sofa bed.",
    "Three goals, one assist.",
    "Two wins, no losses.",
    "Four innings, no runs.",
    "Two killed, one injured in crash.",
    "Five arrested, one charged.",
    "Two judges, one dissent.",
    "Two candidates, one seat.",
    "Two adults, one child.",
    "One carry-on, no checked bags.",
    "Two packages, one damaged.",
    "Three meetings, all cancelled.",
    "Two bugs, one fixed.",
    "Three groups, each of size 20.",
    "Five trials, zero events.",
    "Fig. 3. Two panels, each showing a trial.",
    "the\ntwo families, each paying half.",
]


@pytest.mark.parametrize("text", TERSE_REGISTER)
def test_terse_register_trips_no_structural_rule(text):
    report = run_checks(text, content_type="label")
    assert report["prohibitions_clear"], text
    assert not report["must_clear"], (text, report["must_clear"])


def test_the_caption_rule_stays_rejected():
    """Recorded rejection. Re-proposing it needs a register signal the server
    does not have; see the spec and RULE-HISTORY before reopening."""
    names = {s["name"] for s in load_regex_structures()}
    assert "numeral_contrast_caption" not in names


def test_self_review_carries_the_flagged_shapes():
    """Each shape lives in the rubric with at least one flagged line as its
    attested example."""
    rubric = "\n".join(i["detail"] for i in load_self_review())
    for attested in (
        "so a fix reached people within a day of shipping",
        "came first, and so did the habit of",
        "keep the Figma files behind them tidy",
        "while the rest of the list changes",
        "costs you the design you arrived with",
        "asks me to stand still",
        "One count, four moments",
        "Two adults, one child.",
    ):
        assert attested in rubric, attested


def test_new_rubric_items_are_present_once():
    ids = [item["id"] for item in load_self_review()]
    for item_id in ("so_tail", "backstory_and_self_portrait", "cold_reader_test"):
        assert ids.count(item_id) == 1, item_id


def test_ap069_is_the_caption_example():
    aps = {a["id"]: a for a in json.loads((DATA / "anti_patterns.json").read_text())["patterns"]}
    ap = aps["AP-069"]
    assert ap["before"] == "One count, four moments"
    assert "Not mechanized" in ap["explanation"]
    assert "AP-069" in "\n".join(i.get("history", "") for i in load_self_review())


def test_caveat_records_that_the_flagged_lines_passed():
    caveats = {c["id"]: c for c in json.loads((DATA / "caveats.json").read_text())["core_caveats"]}
    entry = caveats["reviewed_copy_passes_the_checker"]
    # The measurement is maintainer history; the served text keeps the advice.
    assert "2026-11-09" in entry["history"] and "31" in entry["history"]
    assert "none survived" in entry["history"]
    assert "self_review" in entry["explanation"]
