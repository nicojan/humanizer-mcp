"""BS-038 appended_wh_label (2026-08-08, in-the-wild reviewer report).

The label line that appends a second, evaluative element promising significance:
"Method, and why this one", "The rebuild, and why it took nine months". The
mechanizable slice is the WH-appendix on a bounded label line. The open-ended
sibling — a dek that appends a reduced relative clause instead of a WH word
("Reintegration support at the moment of release, and the officer the whole
system turns on.") — is deliberately judgment-only, because separating it from
ordinary coordination needs a parser, not a regex; it lives in self_review.json.

Every negative case below pins a named FP guard: bounded-line anchoring (the
appendix must end the line), a subject-pronoun block on the head so ordinary
prose clauses cannot match, a head-length cap that keeps it label-shaped, and a
short comma-free tail so a full second clause never matches.
"""

import json
import pathlib

import pytest

from src.checker.loader import load_regex_structures
from src.checker.structures import find_regex_structures

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"


def _hits(text: str) -> list[dict]:
    return [
        f
        for f in find_regex_structures(text, load_regex_structures())
        if f["id"] == "BS-038"
    ]


def test_wired_as_a_regex_structure():
    assert "BS-038" in {s["id"] for s in load_regex_structures()}


def test_gate_is_checklist_never_hard():
    s = next(s for s in load_regex_structures() if s["id"] == "BS-038")
    assert s["gate"] == "checklist"


def test_source_example_anti_pattern_exists():
    s = next(s for s in load_regex_structures() if s["id"] == "BS-038")
    ids = {p["id"] for p in json.loads((DATA / "anti_patterns.json").read_text())["patterns"]}
    assert set(s["source_examples"]) <= ids


# --- fires ---
@pytest.mark.parametrize(
    "text",
    [
        "Method, and why this one",
        "## Method, and why this one",
        "# The rebuild, and why it took nine months",
        "The rollout, and how we got here",
        "Scope, and what it costs.",
        "**Method, and why this one**",
        "### Parole supervision, and who carries it",
        "Findings\n\nThe budget, and why it grew\n\nMore text here.",
        "Method, and why this one:",
    ],
)
def test_fires(text):
    assert _hits(text), text


# --- FP guard: subject pronoun in the head (ordinary prose clause) ---
@pytest.mark.parametrize(
    "text",
    [
        "He explained the delay, and why it mattered.",
        "We rebuilt the board, and why that matters.",
        "They shipped on Friday, and what it cost them.",
        "It was a long year, and why nobody noticed.",
    ],
)
def test_pronoun_head_does_not_fire(text):
    assert not _hits(text)


# --- FP guard: the appendix must end the line ---
@pytest.mark.parametrize(
    "text",
    [
        "The panel asked about the method, and why this one, before lunch.",
        "The board met on Tuesday, and why it matters is another question.",
        "The report covers scope, and what it costs, but not the timeline.",
    ],
)
def test_unbounded_appendix_does_not_fire(text):
    assert not _hits(text)


# --- FP guard: ordinary coordination without a WH appendix ---
@pytest.mark.parametrize(
    "text",
    [
        "Method, and Results",
        "The budget, and the timeline",
        "Costs, and the people who pay them",
        "Bread, flour, and the oven",
    ],
)
def test_plain_coordination_does_not_fire(text):
    assert not _hits(text)


# --- FP guard: head must stay label-length ---
def test_very_long_head_does_not_fire():
    head = "the review of the funding of the delivery of the support of the service"
    assert not _hits(f"{head}, and why it matters")


def test_offset_points_at_the_line():
    text = "Intro paragraph.\n\nMethod, and why this one\n\nBody."
    hits = _hits(text)
    assert hits
    assert text[hits[0]["offset"] : hits[0]["offset"] + 30].lstrip().startswith("Method")


def test_redos_safe():
    import time

    payload = ("a " * 100_000) + ", and why it matters"
    t0 = time.monotonic()
    _hits(payload)
    assert time.monotonic() - t0 < 2.0


# --- BS-039 not_but_fragment ---
def _hits39(text: str) -> list[dict]:
    return [
        f
        for f in find_regex_structures(text, load_regex_structures())
        if f["id"] == "BS-039"
    ]


def test_bs039_wired_and_checklist():
    s = next(s for s in load_regex_structures() if s["id"] == "BS-039")
    assert s["gate"] == "checklist"


@pytest.mark.parametrize(
    "text",
    [
        "The handoff broke. Not because the person stopped mattering, but because the officer is reachable.",
        "We changed the form. Not to save time, but to save arguments.",
        "Not a strategy, but a habit.",
        "It is a rule. Not the exception, but the default.",
        "Not for the team, but for the client.",
    ],
)
def test_bs039_fires(text):
    assert _hits39(text), text


# FP guards: a real subject NP after "Not", a non-parallel second limb, and
# mid-sentence correlatives, which are ordinary grammar rather than the tell.
@pytest.mark.parametrize(
    "text",
    [
        "Not all of them agreed, but most did.",
        "Not everyone will like it, but that is fine.",
        "Not a single person moved, but the door opened.",
        "He did not go to the store, but to the park.",
        "Not much happened, but we stayed.",
    ],
)
def test_bs039_does_not_fire(text):
    assert not _hits39(text)


def test_bs039_redos_safe():
    import time

    payload = "Not " + ("a " * 80_000) + ", but a thing."
    t0 = time.monotonic()
    _hits39(payload)
    assert time.monotonic() - t0 < 2.0


# --- the judgment-only sibling lives in the self-review rubric ---
def test_appended_significance_label_is_a_self_review_item():
    items = json.loads((DATA / "self_review.json").read_text())["self_review"]["items"]
    joined = " ".join(items).lower()
    assert "appended" in joined and "label" in joined
