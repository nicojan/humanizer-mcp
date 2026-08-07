"""Curated lexical additions (2026-07-25 research pass). Marketing/promotional
cluster the checker missed: verbs (unlock, unleash, embark, empower, elevate),
adjectives (vibrant, invaluable, unwavering, ever-evolving), and nouns
(treasure trove, plethora, myriad). All surface as must_clear flagged_terms,
auto-wired via load_flagged_terms -> find_flagged_terms. Data-only, no code
change."""

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
        ("This will unlock new revenue streams.", "unlock"),
        ("The update unleashes the full power of the engine.", "unleash"),
        ("We embark on an ambitious rebuild this quarter.", "embark"),
        ("Our mission is to empower every team.", "empower"),
        ("These tips will elevate your writing.", "elevate"),
        ("The city has a vibrant arts scene.", "vibrant"),
        ("Her feedback proved invaluable.", "invaluable"),
        ("They showed unwavering commitment to the goal.", "unwavering"),
        ("In an ever-evolving market, we adapt.", "ever-evolving"),
        ("The archive is a treasure trove of records.", "treasure trove"),
        ("A plethora of options confused the buyers.", "plethora"),
        ("A myriad of factors shaped the result.", "myriad"),
    ],
)
def test_new_lexical_terms_fire(text, term):
    assert term in _terms(text), f"expected {term!r} flagged in {text!r}"


def test_new_lexical_terms_never_block_prohibitions():
    r = run_checks("This will unlock a vibrant, ever-evolving future.", "prose")
    assert r["prohibitions_clear"] is True
