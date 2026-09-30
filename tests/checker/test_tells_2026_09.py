"""BS-042 conjoined_candour_disclaimer and the BS-040 subject-list extension of
the 2026-09-17 round, plus a regression pinning the appositive label as
deliberately unflagged.

BS-042 is scoped to the CONJOINED form only: a comma plus and/but must precede
the frame. That guard is what separates it from the 2026-07-25 rejection of
register-dependent openers. Sentence-initial "I'm not going to pretend I
understand the tax code." is an ordinary hedge, not a performed admission, and
every negative below pins that.

The BS-040 extension adds abstract process and project nouns to the subject
alternation. The object list is unchanged, which is what keeps "carries risk",
"carries a cost" and "carries weight" - ordinary business and legal register -
out of the findings.

The appositive test is a negative regression, not a gap waiting to be filled.
Three attempts to mechanize it are recorded in the 2026-09-17 design doc and in
caveats.labels_are_where_the_tells_hide; the best scored 1/14 false positives
against a standing bar of zero.
"""

import json
import pathlib
import time

import pytest

from src.checker.loader import load_regex_structures
from src.checker.structures import find_regex_structures
from tests.support.fp_corpus import assert_tier1_clear

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"


def _hits(text: str, rule: str) -> list[dict]:
    return [f for f in find_regex_structures(text, load_regex_structures()) if f["id"] == rule]


def test_bs042_wired_as_regex_structure():
    assert "BS-042" in {s["id"] for s in load_regex_structures()}


def test_bs042_gate_is_checklist_never_hard():
    s = next(s for s in load_regex_structures() if s["id"] == "BS-042")
    assert s["gate"] == "checklist"


def test_bs042_source_example_anti_pattern_exists():
    s = next(s for s in load_regex_structures() if s["id"] == "BS-042")
    ids = {p["id"] for p in json.loads((DATA / "anti_patterns.json").read_text())["patterns"]}
    assert set(s["source_examples"]) <= ids


# --- BS-042 fires: the candour beat appended to a finished statement.
@pytest.mark.parametrize(
    "text",
    [
        "The redesign took nine months, and I'm not going to pretend that was the plan.",
        "It shipped late, and I am not going to pretend otherwise.",
        "We lost the account, and I won't pretend it didn't hurt.",
        "The numbers are bad, and I'm not going to sugarcoat them.",
        "That was my call, and I’m not going to pretend it wasn’t.",
        "The first version failed, but I'm not going to claim we saw it coming.",
        "It cost more than we said, and I'm not gonna pretend that's fine.",
        "The estimate was wrong, and I won’t pretend it was close.",
        "We shipped it anyway, and I'm not about to act like that was wise.",
    ],
)
def test_bs042_fires(text):
    assert _hits(text, "BS-042"), text


# --- FP guard: the frame must be APPENDED. Sentence-initial and quoted uses are
# ordinary first-person speech, and flagging them is the flow_over_surface_features
# trap that killed the bare "quiet" flag and "Here's the thing".
@pytest.mark.parametrize(
    "text",
    [
        "I'm not going to pretend I understand the tax code.",
        "I won't pretend it was easy. But it worked.",
        "Look, I'm not going to pretend. This is hard.",
        "She said she was not going to pretend for anyone.",
        "He is not going to claim the prize, and that is his choice.",
        "They asked me to stay, and I am not going to.",
        "The deadline slipped, and I am not happy about it.",
        "We tried three times, and I will not try again.",
        "It rained all week, and I'm not going out in that.",
        "I told the client the truth, and I'd tell them again.",
        "\"I'm not going to pretend,\" she said, and left.",
    ],
)
def test_bs042_does_not_fire(text):
    assert not _hits(text, "BS-042"), text


def test_bs042_offset_points_at_the_conjunction():
    text = "The redesign took nine months, and I'm not going to pretend that was the plan."
    hits = _hits(text, "BS-042")
    assert hits
    assert text[hits[0]["offset"] :].startswith(",")


def test_bs042_redos_safe():
    pathological = "I am not going to " * 20000
    start = time.perf_counter()
    _hits(pathological, "BS-042")
    assert (time.perf_counter() - start) < 1.0


# --- BS-040 extension: abstract process and project nouns as the subject.
@pytest.mark.parametrize(
    "text",
    [
        "The rebuild carries the argument for the whole quarter.",
        "The redesign carries the story of what changed.",
        "Our rollout carries the message to every region.",
        "The decision carries its own logic.",
        "That approach carries the thesis of the paper.",
        "The migration carries the lessons from the last one.",
        "The pilot carries the case for the whole programme.",
    ],
)
def test_bs040_abstract_process_subject_fires(text):
    assert _hits(text, "BS-040"), text


# --- FP guard for the extension: an abstract subject with a non-informational
# object is ordinary business and legal register, not a tell. The object list is
# unchanged by this round, which is what holds the line.
@pytest.mark.parametrize(
    "text",
    [
        "The delay carries real consequences for the team.",
        "The project carries significant risk.",
        "Every change carries a cost.",
        "The decision carries weight with the board.",
        "This approach carries a penalty if it fails.",
        "The rollout carries the servers to the new datacentre.",
        "The migration carries the database over the weekend.",
        "The study carries a margin of error of three points.",
        "The pilot carries two passengers.",
        "The program carries a five-year warranty.",
    ],
)
def test_bs040_abstract_subject_ordinary_register_does_not_fire(text):
    assert not _hits(text, "BS-040"), text


# --- Negative regression. The appositive label is a known, deliberate gap: it
# stays a self_review judgment item. This test documents that and will fail
# loudly if a later round mechanizes it without revisiting the design doc.
@pytest.mark.parametrize(
    "text",
    [
        "Reintegration support at the moment of release, and the officer the whole system turns on.",
        "The baker bought bread, and the flour that makes it.",
        "The vendor ships on Tuesday, and the invoice follows.",
    ],
)
def test_appositive_label_remains_unmechanized(text):
    assert not find_regex_structures(text, load_regex_structures()), text


@pytest.mark.parametrize("rule", ["BS-040", "BS-042"])
def test_no_false_positives_on_tier1_human_corpus(rule):
    """Tier 1 bar: zero findings on the modern matched-register corpus.

    BS-040 and BS-042 are per-sentence shapes, so Tier 1 is the tier that can
    answer for them. Tier 2 measures both at 0.0 per 10k as well (see
    docs/RULE-HISTORY.md, 2026-09-18).
    """
    assert_tier1_clear(lambda text: _hits(text, rule), rule)
