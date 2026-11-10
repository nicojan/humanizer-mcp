"""BS-024 vague_authority_attribution: appeals to an unnamed authority
('Researchers say...', 'Studies show...', 'Experts agree...', 'It is widely
believed...', 'Many argue...'). Regex, gate=checklist, auto-wired. The verb
list is scoped to the epistemic-claim frames, so a named/specific reference
with a concrete action ('The researchers at MIT published...') does not match."""

import pytest

from src.checker import run_checks
from src.checker.loader import load_regex_structures
from src.checker.structures import find_regex_structures


def _hits(text: str) -> list[dict]:
    return [
        f
        for f in find_regex_structures(text, load_regex_structures())
        if f["id"] == "BS-024"
    ]


def test_bs_024_is_wired_as_a_regex_structure():
    assert "BS-024" in {s["id"] for s in load_regex_structures()}


@pytest.mark.parametrize(
    "text",
    [
        "Researchers say the trend is real.",
        "Studies show a clear link between the two.",
        "Experts agree the cause is structural.",
        "It is widely believed that the practice is safe.",
        "Many argue the opposite is true.",
        "Research suggests otherwise.",
        "Scientists have found the effect persists.",
    ],
)
def test_vague_attributions_are_flagged(text):
    assert _hits(text), f"expected BS-024 to fire on {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "The researchers at MIT published their raw data last week.",
        "She studies marine biology at the university.",
        "Studies of the region began in the 1990s.",
        "Our research team built the tool in six weeks.",
        "The experts we hired reviewed the contract.",
    ],
)
def test_named_or_specific_references_are_not_flagged(text):
    assert not _hits(text), f"BS-024 false-positive on {text!r}"


def test_surfaces_in_must_clear_never_hard():
    report = run_checks("Studies show the method works well.", "prose")
    assert any(f.get("id") == "BS-024" for f in report["must_clear"])
    assert report["prohibitions_clear"] is True


# The headline attribution (2026-11-09, found by the terse-register set). A news
# headline ends "..., economists say" with no full stop and names its sources in
# the story, so "name the source" is the wrong fix there. Only that form is
# declined: a comma, a group noun, say/says, then the end of the line.
@pytest.mark.parametrize(
    "text",
    [
        "Not a recession, but close, economists say",
        "Rates to hold through spring, analysts say",
        "Housing shortage to worsen, experts say\nDetails on page 4.",
        "Rents fall again, economists say\r\n",
    ],
)
def test_a_headline_attribution_is_not_flagged(text):
    assert not _hits(text)


@pytest.mark.parametrize(
    "text",
    [
        # The same frame in body prose, with a full stop, is the tell.
        "Remote work boosts productivity, experts say.",
        "Experts say remote work boosts productivity",
        "Remote work, experts say, boosts productivity.",
        "Remote work boosts productivity, experts argue",
    ],
)
def test_the_body_attribution_still_is(text):
    assert _hits(text)
