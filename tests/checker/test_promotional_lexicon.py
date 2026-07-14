"""Lexical additions (2026 in-the-wild + Wikipedia 'Signs of AI writing'):
AI-overused sentence openers (Additionally / Notably / Importantly /
Consequently) join the flagged_transitions family, and the promotional/travel-
guide register (bustling, breathtaking, hidden gem) joins the flagged
adjectives/nouns. All surface as must_clear flagged_terms, auto-wired via
load_flagged_terms -> find_flagged_terms. Data-only, no code change."""

import pytest

from src.checker import run_checks


def _terms(text: str) -> set[str]:
    r = run_checks(text, "prose")
    return {
        f["term"].lower() for f in r["must_clear"] if f.get("type") == "flagged_term"
    }


@pytest.mark.parametrize(
    "text,term",
    [
        ("Additionally, we shipped the new dashboard.", "additionally"),
        ("Consequently, the numbers climbed.", "consequently"),
        ("Notably, retention improved this quarter.", "notably"),
        ("Importantly, we validated the fix end to end.", "importantly"),
        ("The bustling downtown core drew crowds.", "bustling"),
        ("A breathtaking view opened up over the ridge.", "breathtaking"),
        ("The cafe is a real hidden gem.", "hidden gem"),
    ],
)
def test_flagged_terms_fire(text, term):
    assert term in _terms(text), f"expected {term!r} flagged in {text!r}"


def test_flagged_terms_never_block_prohibitions():
    r = run_checks("Additionally, the bustling market was a hidden gem.", "prose")
    assert r["prohibitions_clear"] is True
