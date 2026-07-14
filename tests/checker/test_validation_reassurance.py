"""BS-023 validation_reassurance: direct second-person reassurance frames
('You're not alone.', 'You're not imagining it.', 'It's not just you.') — the
single most-cited *new* 2026 AI tell (unsolicited validation). Regex,
gate=checklist, auto-wired via the loader. High-precision: it fires only on the
fixed 'you're not <predicate>' / 'it's not just you' frames, so ordinary
negations ('You're not sure yet.') never match."""

import pytest

from src.checker import run_checks
from src.checker.loader import load_regex_structures
from src.checker.structures import find_regex_structures


def _hits(text: str) -> list[dict]:
    return [
        f
        for f in find_regex_structures(text, load_regex_structures())
        if f["id"] == "BS-023"
    ]


def test_bs_023_is_wired_as_a_regex_structure():
    assert "BS-023" in {s["id"] for s in load_regex_structures()}


@pytest.mark.parametrize(
    "text",
    [
        "You're not alone.",
        "You're not imagining it.",
        "You're not broken.",
        "You are not crazy.",
        "You're not failing.",
        "And honestly, it's not just you.",
        "Work is hard right now. You're not alone.",
    ],
)
def test_validation_frames_are_flagged(text):
    assert _hits(text), f"expected BS-023 to fire on {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "You're not sure what to do next.",
        "You are not authorized to view this page.",
        "It's not just about the money, it's the principle.",
        "You're not going to believe what happened.",
        "The build is not broken anymore.",
    ],
)
def test_ordinary_negations_are_not_flagged(text):
    assert not _hits(text), f"BS-023 false-positive on {text!r}"


def test_surfaces_in_must_clear_never_hard():
    report = run_checks("You've got this. You're not alone.", "prose")
    assert any(f.get("id") == "BS-023" for f in report["must_clear"])
    assert report["prohibitions_clear"] is True
