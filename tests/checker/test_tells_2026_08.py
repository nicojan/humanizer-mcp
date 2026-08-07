"""BS-031..037 (2026-08-06 research pass, docs/proposed-rules-2026-08-06.md).

Metaphorical 'carry' (BS-031, the in-the-wild trigger for this batch), the
'Honestly?' candour fragment (BS-032), the 'quiet X / quietly reshaping'
collocation (BS-033), the 'While X has benefits, it also carries risks'
balancing hedge (BS-034), tidy internal cross-references (BS-035), the
'Let that sink in.' deepening invitation (BS-036), and the withheld-insight
teaser (BS-037). All regex, gate=checklist, auto-wired via the loader, so this
batch is data-only with no code change.

Every negative case below pins a named FP guard from the design doc: abstract-
object allow-lists (BS-031), bounded-fragment anchoring (BS-032), collocation
allow-lists rather than a bare word flag (BS-033), verb+object allow-lists
(BS-034), and the withheld-insight claim rather than the bare discourse marker
(BS-037).
"""

import pytest

from src.checker.loader import load_regex_structures
from src.checker.structures import find_regex_structures

IDS = ["BS-031", "BS-032", "BS-033", "BS-034", "BS-035", "BS-036", "BS-037"]


def _hits(text: str, bs_id: str) -> list[dict]:
    return [
        f
        for f in find_regex_structures(text, load_regex_structures())
        if f["id"] == bs_id
    ]


@pytest.mark.parametrize("bs_id", IDS)
def test_wired_as_regex_structures(bs_id):
    assert bs_id in {s["id"] for s in load_regex_structures()}


@pytest.mark.parametrize("bs_id", IDS)
def test_gate_is_checklist_never_hard(bs_id):
    s = next(s for s in load_regex_structures() if s["id"] == bs_id)
    assert s["gate"] == "checklist"


# --- BS-031 metaphorical_carry ---
@pytest.mark.parametrize(
    "text",
    [
        "The layout carries the weight of the argument.",
        "That single paragraph carried the burden of the whole case.",
        "The gesture carries the meaning, not the caption.",
        "Eight words to carry.",
        "Three lines to carry the whole act.",
        "It leaves you with one sentence to carry.",
    ],
)
def test_bs031_fires(text):
    assert _hits(text, "BS-031")


@pytest.mark.parametrize(
    "text",
    [
        "The box was too heavy to carry.",
        "The truck carries the load to the depot.",
        "Each barge carried the freight downriver.",
        "She had to carry the groceries up four flights.",
        "Carry the two and add the remainder.",
        "The carriers arrive on Tuesday.",
        "We carry the part in three sizes.",
        "Porters carry the luggage to the room.",
        "He offered to carry it for her.",
    ],
)
def test_bs031_ignores_literal_carrying(text):
    assert not _hits(text, "BS-031")


# --- BS-032 honestly_fragment_opener ---
@pytest.mark.parametrize(
    "text",
    [
        "Honestly? Most people never follow up.",
        "The plan looked fine. Frankly? It was not.",
        "Truthfully? Consistency beats talent.",
        "Real talk? Nobody reads the appendix.",
    ],
)
def test_bs032_fires(text):
    assert _hits(text, "BS-032")


@pytest.mark.parametrize(
    "text",
    [
        '"Honestly?" she said, and put the letter down.',
        "Did she answer honestly? We never found out.",
        "Honestly, most people never follow up.",
        "I asked him to answer frankly? No, I insisted on it.",
    ],
)
def test_bs032_ignores_quoted_and_embedded(text):
    assert not _hits(text, "BS-032")


# --- BS-033 quiet_prestige_modifier ---
@pytest.mark.parametrize(
    "text",
    [
        "She led with quiet confidence.",
        "It was a quiet rebellion against the style guide.",
        "The team is quietly reshaping how the org ships.",
        "They quietly became the largest supplier in the region.",
        "There is a quiet power in saying nothing.",
    ],
)
def test_bs033_fires(text):
    assert _hits(text, "BS-033")


@pytest.mark.parametrize(
    "text",
    [
        "It was a quiet room with one window.",
        "She quietly closed the door behind her.",
        "The quiet street filled up by eight.",
        "He spoke quietly so the baby would not wake.",
        "A quiet morning, and then the alarm.",
    ],
)
def test_bs033_ignores_ordinary_quiet(text):
    assert not _hits(text, "BS-033")


# --- BS-034 concessive_balance_hedge ---
@pytest.mark.parametrize(
    "text",
    [
        "While automation has benefits, it also carries risks.",
        "While the approach is fast, it still poses serious challenges.",
        "While remote work suits many teams, it comes with real trade-offs.",
        "While the tool is free, it presents certain limitations.",
        "While the migration is overdue, it also raises concerns.",
    ],
)
def test_bs034_fires(text):
    assert _hits(text, "BS-034")


@pytest.mark.parametrize(
    "text",
    [
        "While the build ran, I made coffee.",
        "While she waited, it started to rain.",
        "While automation has benefits, we shipped it anyway.",
        "While the approach is fast, it also broke two rollbacks in week one.",
        "The risks are real, though the benefits are larger.",
    ],
)
def test_bs034_ignores_ordinary_concessives(text):
    assert not _hits(text, "BS-034")


# --- BS-035 internal_cross_reference ---
@pytest.mark.parametrize(
    "text",
    [
        "As mentioned above, the migration depends on the schema freeze.",
        "As noted earlier, the queue is the bottleneck.",
        "As we discussed previously, the deadline moved.",
        "As stated before, the API is read-only.",
        "As I said earlier, nobody owns this file.",
    ],
)
def test_bs035_fires(text):
    assert _hits(text, "BS-035")


@pytest.mark.parametrize(
    "text",
    [
        "See section 4 for the schema freeze.",
        "As the schema freeze approaches, the migration stalls.",
        "The note above explains the freeze.",
        "As we discussed the options, the deadline moved.",
    ],
)
def test_bs035_ignores_ordinary_reference(text):
    assert not _hits(text, "BS-035")


# --- BS-036 deepening_invitation ---
@pytest.mark.parametrize(
    "text",
    [
        "Only three of the twelve shipped. Let that sink in.",
        "Do you want to sit with that for a while?",
        "Are you ready to go deeper?",
        "Read that again.",
        "Sit with this for a moment before you answer.",
    ],
)
def test_bs036_fires(text):
    assert _hits(text, "BS-036")


@pytest.mark.parametrize(
    "text",
    [
        "The water will sink in overnight.",
        "Sit with her until the doctor comes.",
        "Are you ready to go?",
        "I had to read that twice.",
    ],
)
def test_bs036_ignores_literal_use(text):
    assert not _hits(text, "BS-036")


# --- BS-037 withheld_insight_teaser ---
@pytest.mark.parametrize(
    "text",
    [
        "Here's the kicker: the queue was empty the whole time.",
        "The part most people miss is the review step.",
        "This is what nobody tells you about hiring.",
        "The thing most people get wrong is the ordering.",
        "The secret no one tells you is that it is mostly waiting.",
    ],
)
def test_bs037_fires(text):
    assert _hits(text, "BS-037")


@pytest.mark.parametrize(
    "text",
    [
        "Here's the thing: the queue was empty.",
        "Most people miss the review step.",
        "Nobody tells you anything around here.",
        "Here's the report you asked for.",
        "The part I miss is the commute.",
    ],
)
def test_bs037_ignores_bare_markers(text):
    assert not _hits(text, "BS-037")
