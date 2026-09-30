"""BS-040 artifact_subject_carry and BS-041 stale_figure_of_speech, plus the
data-side additions of the 2026-08-10 Orwell round.

BS-040 closes the gap between BS-031, which matches only the fixed abstract
collocations ("carries the weight|burden|meaning"), and the open
abstract-subject family that stays a self_review item. The mechanizable slice
requires BOTH ends: an artifact-noun subject head and an informational object
head. Every negative below pins that second requirement, because most of the
artifact nouns are also load-bearing objects in the physical world (a column
carries a roof, a frame carries glass, a table carries plates).

BS-041 is Orwell's first rule over a closed list of figures. It is house style
rather than an authorship signal, so the eval corpus proves nothing either way
about recall; the negatives here pin the two literal-sense guards instead.
"""

import json
import pathlib

import pytest

from src.checker.loader import load_flagged_terms, load_regex_structures
from src.checker.structures import find_regex_structures
from tests.support.fp_corpus import assert_tier1_clear

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"


def _hits(text: str, rule: str) -> list[dict]:
    return [f for f in find_regex_structures(text, load_regex_structures()) if f["id"] == rule]


@pytest.mark.parametrize("rule", ["BS-040", "BS-041"])
def test_wired_as_regex_structures(rule):
    assert rule in {s["id"] for s in load_regex_structures()}


@pytest.mark.parametrize("rule", ["BS-040", "BS-041"])
def test_gate_is_checklist_never_hard(rule):
    s = next(s for s in load_regex_structures() if s["id"] == rule)
    assert s["gate"] == "checklist"


@pytest.mark.parametrize("rule", ["BS-040", "BS-041"])
def test_source_example_anti_patterns_exist(rule):
    s = next(s for s in load_regex_structures() if s["id"] == rule)
    ids = {p["id"] for p in json.loads((DATA / "anti_patterns.json").read_text())["patterns"]}
    assert set(s["source_examples"]) <= ids


# --- BS-040 fires: the six sentences from the 2026-08-10 in-the-wild report,
# each of which returned prohibitions_clear with zero findings before this rule.
@pytest.mark.parametrize(
    "text",
    [
        "The deck carries one still of the dashboard.",
        "Each board carries its own title, rule, and legend.",
        "The margin rail carries the tags.",
        "Slide 18 carries the business model.",
        "The presenter notes carry the argument.",
        "Section 06 carries the lessons.",
        "The page carries a single argument.",
        "Every diagram carries its own legend.",
        "The rail carried the tags all the way down.",
        "The report carries the data everyone quotes.",
        "The prototype carries the whole product story.",
    ],
)
def test_bs040_fires(text):
    assert _hits(text, "BS-040"), text


# --- FP guard: the object must be informational. These subjects are all on the
# artifact list and all literally bear something, so only the object list keeps
# them out.
@pytest.mark.parametrize(
    "text",
    [
        "The column carries the roof and two floors above it.",
        "The frame carries the glass without a bracket.",
        "The table carries the plates for eight.",
        "The board carries the load to the second storey.",
        "The card carries an account number on the back.",
        "The tile carries the weight of the stove.",
    ],
)
def test_bs040_literal_object_does_not_fire(text):
    assert not _hits(text, "BS-040")


# --- FP guard: the subject must be an artifact noun sitting immediately before
# the verb. Vehicles, containers, people and infrastructure are all excluded,
# including the retail "carries that brand" sense.
@pytest.mark.parametrize(
    "text",
    [
        "The truck carries the load to the depot.",
        "The store carries that brand in three sizes.",
        "The courier carries the documents to the registry.",
        "The folder carries the notes from every interview.",
        "The envelope carries the report and nothing else.",
        "The ledger carries the names of everyone released.",
        "Cables carry the data between the two buildings.",
        "She carries the argument every time they meet.",
        "He carried the boards up the stairs.",
        "The note carries interest at four percent.",
    ],
)
def test_bs040_non_artifact_subject_does_not_fire(text):
    assert not _hits(text, "BS-040")


def test_bs040_offset_points_at_the_subject():
    text = "Intro paragraph here.\n\nEach board carries its own title.\n"
    hits = _hits(text, "BS-040")
    assert hits
    assert text[hits[0]["offset"] :].startswith("board")


def test_bs040_redos_safe():
    import time

    payload = "the board carries the " * 20_000
    t0 = time.monotonic()
    _hits(payload, "BS-040")
    assert time.monotonic() - t0 < 2.0


# --- BS-041 fires ---
@pytest.mark.parametrize(
    "text",
    [
        "It moves the needle on readiness.",
        "The federal purse would feel it.",
        "We started with the low-hanging fruit.",
        "That is the tip of the iceberg.",
        "It is a double-edged sword.",
        "At the end of the day, what matters is the release date.",
        "The change raised the bar for everyone.",
        "There are many moving parts here.",
        "They took the lion's share of the budget.",
        "Nobody wanted to boil the ocean.",
        "This is the elephant in the room.",
        "It was a perfect storm of scheduling and funding.",
        "They want a level playing field.",
        "The team hit the ground running.",
        "It costs the taxpayer's dime either way.",
    ],
)
def test_bs041_fires(text):
    assert _hits(text, "BS-041"), text


# --- FP guard: the literal senses. "raise the bar" must be terminal or take
# for/on/across; "at the end of the day" must sit in the filler frame.
@pytest.mark.parametrize(
    "text",
    [
        "At the end of the day we walked back to the car.",
        "At the end of the day the gates close at six.",
        "She raised the bar three inches and jumped again.",
        "He raised the bar two notches before his last attempt.",
        "The needle moved two millimetres on the gauge.",
        "The fruit hung low over the fence.",
        "We saw an iceberg from the deck.",
        "The sword was double-edged and heavy in his hand.",
        "The playing field was level after the rain.",
        "The moving parts arrived in a crate.",
    ],
)
def test_bs041_literal_sense_does_not_fire(text):
    assert not _hits(text, "BS-041")


def test_bs041_redos_safe():
    import time

    payload = ("at the end of the day " * 20_000) + "the thing is done."
    t0 = time.monotonic()
    _hits(payload, "BS-041")
    assert time.monotonic() - t0 < 2.0


# --- zero false positives on the genuine-human eval corpus. For BS-040 this is
# the repo's standard FP gate. For BS-041 it is weaker evidence than usual: the
# figures are house style and human writing uses them, so a hit here would be a
# true positive under the rule and a reason to reconsider the rule's gate, not a
# detector bug. Recorded either way.


@pytest.mark.parametrize("rule", ["BS-040", "BS-041"])
def test_no_false_positives_on_tier1_human_corpus(rule):
    """Tier 1 bar: zero findings on the modern matched-register corpus.

    BS-040 and BS-041 are per-sentence shapes. Tier 2 measures BS-040 at 0.0
    and BS-041 at 0.2 per 10k (see docs/RULE-HISTORY.md, 2026-09-18).
    """
    assert_tier1_clear(lambda text: _hits(text, rule), rule)


# --- the Orwell data additions ---
def test_orwell_block_present_and_shaped():
    lex = json.loads((DATA / "lexical_patterns.json").read_text())
    orwell = lex["orwell"]
    assert [r["rule"] for r in orwell["rules"]] == [1, 2, 3, 4, 5, 6]
    assert orwell["long_word_substitutions"] and orwell["padding_phrases"]
    assert "define" in orwell["jargon_carve_out"]["rule"].lower()


def test_orwell_is_a_protocol_phase_after_verification():
    phases = json.loads((DATA / "foundation.json").read_text())["application_protocol"]["phases"]
    orwell = [p for p in phases if "orwell" in p["name"].lower()]
    assert len(orwell) == 1
    verification = next(p for p in phases if "humanizer_check_text" in str(p["tools"]))
    assert orwell[0]["phase"] > verification["phase"]
    assert "lexical_patterns.orwell.rules[*]" in orwell[0]["rule_paths"]


def test_orwell_phase_requires_a_recheck_after_trimming():
    phases = json.loads((DATA / "foundation.json").read_text())["application_protocol"]["phases"]
    orwell = next(p for p in phases if "orwell" in p["name"].lower())
    assert "re-run" in orwell["stop_condition"].lower()


def test_plainness_is_a_self_review_item():
    items = json.loads((DATA / "self_review.json").read_text())["self_review"]["items"]
    joined = " ".join(items).lower()
    assert "orwell" in joined and "passive" in joined


def test_long_word_verbs_are_flagged_terms():
    terms = {t["term"] for t in load_flagged_terms()}
    assert {"commence", "ascertain", "necessitate"} <= terms


@pytest.mark.parametrize(
    "caveat", ["jargon_substitution_loses_meaning", "per_section_checks_miss_document_budgets"]
)
def test_new_caveats_present(caveat):
    ids = {c["id"] for c in json.loads((DATA / "caveats.json").read_text())["core_caveats"]}
    assert caveat in ids


def test_document_budget_named_in_the_verification_phase():
    phases = json.loads((DATA / "foundation.json").read_text())["application_protocol"]["phases"]
    verification = next(p for p in phases if "humanizer_check_text" in str(p["tools"]))
    assert "assembled" in verification["stop_condition"].lower()
