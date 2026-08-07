"""BS-026..030 phrase-frame tells (2026-07-25 research pass, docs/proposed-rules-
2026-07-25.md). Five fixed AI phrase frames the checker missed: the
'When it comes to X,' opener (BS-026), the 'In a world where...' world-state
opener (BS-027), the 'plays a pivotal role in' template (BS-028), the
'That's where X comes in.' marketing pivot (BS-029), and the 'If you've ever
struggled with...' empathy opener (BS-030). All regex, gate=checklist,
auto-wired via the loader. Data-only, no code change. FP guards: sentence-
boundary anchoring, fixed pivot tokens, and terminal scoping keep ordinary
prose clear."""

import pytest

from src.checker import run_checks
from src.checker.loader import load_regex_structures
from src.checker.structures import find_regex_structures


def _hits(text: str, bs_id: str) -> list[dict]:
    return [
        f
        for f in find_regex_structures(text, load_regex_structures())
        if f["id"] == bs_id
    ]


@pytest.mark.parametrize("bs_id", ["BS-026", "BS-027", "BS-028", "BS-029", "BS-030"])
def test_new_frames_are_wired_as_regex_structures(bs_id):
    assert bs_id in {s["id"] for s in load_regex_structures()}


# --- BS-026 when_it_comes_to_opener ---
@pytest.mark.parametrize(
    "text",
    [
        "When it comes to security, the system holds up well.",
        "When it comes to pricing, we keep it simple.",
        "The plan was set. When it comes to execution, timing matters.",
    ],
)
def test_bs026_fires(text):
    assert _hits(text, "BS-026"), f"expected BS-026 on {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "She knew when it comes to a vote it would fail.",
        "I'll decide when it comes to that.",
        "Ask him when it comes to budgets.",
    ],
)
def test_bs026_no_false_positive(text):
    assert not _hits(text, "BS-026"), f"BS-026 false-positive on {text!r}"


# --- BS-027 world_state_opener ---
@pytest.mark.parametrize(
    "text",
    [
        "In a world where threats evolve fast, teams need better tools.",
        "In an era of remote work, culture is hard to build.",
        "In an age where data is king, privacy suffers.",
        "In a time of constant change, adaptability wins.",
    ],
)
def test_bs027_fires(text):
    assert _hits(text, "BS-027"), f"expected BS-027 on {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "We live in a world with many options.",
        "The film is set in a world of magic.",
        "He grew up in an age of typewriters, before computers.",
    ],
)
def test_bs027_no_false_positive(text):
    assert not _hits(text, "BS-027"), f"BS-027 false-positive on {text!r}"


# --- BS-028 pivotal_role_frame ---
@pytest.mark.parametrize(
    "text",
    [
        "Monitoring plays a pivotal role in catching problems early.",
        "It played a key role in the win.",
        "Feedback plays a central role in the process.",
        "The board plays a critical role in oversight.",
    ],
)
def test_bs028_fires(text):
    assert _hits(text, "BS-028"), f"expected BS-028 on {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "The actors play a role in the story.",
        "They played a supporting role in the film.",
        "Children play a game in the yard.",
    ],
)
def test_bs028_no_false_positive(text):
    assert not _hits(text, "BS-028"), f"BS-028 false-positive on {text!r}"


# --- BS-029 solution_pivot ---
@pytest.mark.parametrize(
    "text",
    [
        "That's where our platform comes in.",
        "This is where we come in.",
        "That's where the API comes in.",
    ],
)
def test_bs029_fires(text):
    assert _hits(text, "BS-029"), f"expected BS-029 on {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "That's where I grew up, and it comes in handy.",
        "This is where we live.",
        "That's where the road ends.",
    ],
)
def test_bs029_no_false_positive(text):
    assert not _hits(text, "BS-029"), f"BS-029 false-positive on {text!r}"


# --- BS-030 empathy_conditional_opener ---
@pytest.mark.parametrize(
    "text",
    [
        "If you've ever struggled with slow deploys, you know the pain.",
        "If you have ever wondered why, read on.",
        "If you've ever felt stuck, this is for you.",
    ],
)
def test_bs030_fires(text):
    assert _hits(text, "BS-030"), f"expected BS-030 on {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "If you've ever been to Paris, you know the traffic.",
        "Tell me if you've ever struggled with this.",
        "If you've ever seen a comet, count yourself lucky.",
    ],
)
def test_bs030_no_false_positive(text):
    assert not _hits(text, "BS-030"), f"BS-030 false-positive on {text!r}"


def test_frames_surface_in_must_clear_never_hard():
    report = run_checks(
        "When it comes to speed, we win. That's where our tool comes in.", "prose"
    )
    ids = {f.get("id") for f in report["must_clear"]}
    assert "BS-026" in ids
    assert "BS-029" in ids
    assert report["prohibitions_clear"] is True
