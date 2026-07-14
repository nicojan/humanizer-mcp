"""BS-025 question_fragment_cadence: the 'The best part? It's this.' rhetorical
tic — a sentence-initial determiner-led noun-phrase fragment ending in '?',
immediately answered by a short sentence. Regex, gate=checklist, auto-wired.
Scoped to a determiner-led NP of <=3 words so WH-questions ('What is the best
part?') and mid-sentence questions ('Did you see the result?') never match."""

import pytest

from src.checker import run_checks
from src.checker.loader import load_regex_structures
from src.checker.structures import find_regex_structures


def _hits(text: str) -> list[dict]:
    return [
        f
        for f in find_regex_structures(text, load_regex_structures())
        if f["id"] == "BS-025"
    ]


def test_bs_025_is_wired_as_a_regex_structure():
    assert "BS-025" in {s["id"] for s in load_regex_structures()}


@pytest.mark.parametrize(
    "text",
    [
        "The best part? It's the simplicity.",
        "The result? A total win for the team.",
        "My advice? Take the job.",
        "The catch? You pay upfront.",
        "We shipped it Friday. The kicker? It actually worked.",
    ],
)
def test_question_fragment_cadence_is_flagged(text):
    assert _hits(text), f"expected BS-025 to fire on {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "What is the best part of this feature?",
        "Did you see the result? It works fine.",
        "Why does the plan work? Because it is simple.",
        "The plan is complete and everyone is happy.",
        "Is the result good enough to ship?",
    ],
)
def test_full_and_midsentence_questions_are_not_flagged(text):
    assert not _hits(text), f"BS-025 false-positive on {text!r}"


def test_surfaces_in_must_clear_never_hard():
    report = run_checks("The best part? It's the simplicity.", "prose")
    assert any(f.get("id") == "BS-025" for f in report["must_clear"])
    assert report["prohibitions_clear"] is True
