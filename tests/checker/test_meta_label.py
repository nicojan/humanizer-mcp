"""BS-022 meta_label: a standalone meta-label line/heading that names the
artifact's own format or length instead of its subject ('in 200 words',
'in brief', 'at a high level'). Regex, gate=checklist, auto-wired via the
loader. The detector fires ONLY on a bounded standalone label, never an
embedded use — that terminal-only guard is what keeps false positives near
zero for the embedding-prone phrases ('at a high level', 'to put it simply').
"""

import pytest

from src.checker import run_checks
from src.checker.loader import load_regex_structures
from src.checker.structures import find_regex_structures


def _meta_label_hits(text: str) -> list[dict]:
    return [
        f
        for f in find_regex_structures(text, load_regex_structures())
        if f["id"] == "BS-022"
    ]


def test_bs_022_is_wired_as_a_regex_structure():
    ids = {s["id"] for s in load_regex_structures()}
    assert "BS-022" in ids


@pytest.mark.parametrize(
    "text",
    [
        "In brief.",
        "In 200 words",
        "In 200 words\n\nThe direction problem",
        "The short version.",
        "The short of it.",
        "The gist:",
        "A quick summary",
        "At a high level.",
        "To put it simply.",
        "Some intro.\nIn short.\nMore text here.",
    ],
)
def test_standalone_meta_labels_are_flagged(text):
    assert _meta_label_hits(text), f"expected BS-022 to fire on {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "At a high level, the system does X.",
        "To put it simply, this works fine.",
        "I explained it in brief to the team.",
        "We shipped the gist of the plan.",
        "Here is a quick summary of what happened next.",
        "The report was written in 200 words of dense jargon.",
    ],
)
def test_embedded_uses_are_not_flagged(text):
    assert not _meta_label_hits(text), f"BS-022 false-positive on {text!r}"


def test_tldr_is_deliberately_excluded():
    assert not _meta_label_hits("TL;DR")
    assert not _meta_label_hits("TL;DR:")


def test_meta_label_surfaces_in_must_clear_report():
    report = run_checks("In 200 words\n\nThe direction problem.", "prose")
    assert any(f.get("id") == "BS-022" for f in report["must_clear"])
    # It is a checklist tell, never a hard prohibition.
    assert report["prohibitions_clear"] is True
