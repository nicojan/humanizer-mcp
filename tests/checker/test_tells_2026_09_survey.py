"""The 2026-09-17 survey round: BS-043..BS-048 plus the BS-027 and BS-035
pattern extensions and the lexical additions.

The headline rule is copula avoidance, which four independent sources name and
which the checker had no coverage of at all. The verb list deliberately does
NOT ship whole: `functions as`, `operates as`, `comprises`, `encompasses`,
`constitutes` and `resides` all have strong literal senses, and a rejection
probe found 8/8 of their uses legitimate. Those are pinned below as a negative
regression so a later round does not add them back without re-probing.

Every FP guard in this file was found by probing, not by guessing:
- BS-043's role-object exclusion needs a three-token window, because the role
  word is often not adjacent to the determiner ("the Labour candidate").
- BS-046 requires a determiner, which is what separates the AI triple
  ("Not a bug. Not a feature.") from ordinary human emphasis ("Not now. Not
  ever.", "Not bad. Not great.").
- The BS-035 extension requires a following comma, after a probe fired on
  "As we have seen the results, we can decide." where the verb takes an object.
"""

import json
import pathlib
import time

import pytest

from src.checker.loader import load_flagged_terms, load_regex_structures
from src.checker.structures import find_regex_structures
from tests.support.fp_corpus import assert_tier1_clear

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"

NEW = ["BS-043", "BS-044", "BS-045", "BS-046", "BS-047", "BS-048"]


def _hits(text: str, rule: str) -> list[dict]:
    return [f for f in find_regex_structures(text, load_regex_structures()) if f["id"] == rule]


@pytest.mark.parametrize("rule", NEW)
def test_wired_as_regex_structures(rule):
    assert rule in {s["id"] for s in load_regex_structures()}


@pytest.mark.parametrize("rule", NEW)
def test_gate_is_checklist_never_hard(rule):
    s = next(s for s in load_regex_structures() if s["id"] == rule)
    assert s["gate"] == "checklist"


@pytest.mark.parametrize("rule", NEW)
def test_source_example_anti_patterns_exist(rule):
    s = next(s for s in load_regex_structures() if s["id"] == rule)
    ids = {p["id"] for p in json.loads((DATA / "anti_patterns.json").read_text())["patterns"]}
    assert set(s["source_examples"]) <= ids


# --- BS-043 copula avoidance -------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "The library serves as the oldest building on campus.",
        "Gallery 825 stands as the exhibition space for the association.",
        "The report serves as a guide for new staff.",
        "The building stands as a monument to the era.",
        "The memo serves as the record of what was agreed.",
        "The pilot stands as the clearest evidence we have.",
        "The deck serves as a reminder to every member of staff.",
    ],
)
def test_bs043_fires(text):
    assert _hits(text, "BS-043"), text


@pytest.mark.parametrize(
    "text",
    [
        "She serves as chair of the committee.",
        "He served as interim director for a year.",
        "Marie serves as the liaison between the two teams.",
        "He stands as tall as his father.",
        "The candidate stands as an independent.",
        "The soup served as dinner that night.",
        "She has served as a volunteer since 2019.",
        "He serves as a member of the tribunal.",
        "She stood as the Labour candidate in 2019.",
        "The trainee serves as a backup on night shifts.",
        "He served as a witness at the hearing.",
        "She serves as the acting chief financial officer.",
        "He stood as the Green Party candidate last spring.",
        "They serve as the elected student representative.",
    ],
)
def test_bs043_role_and_literal_senses_do_not_fire(text):
    assert not _hits(text, "BS-043"), text


@pytest.mark.parametrize(
    "text",
    [
        "The capacitor functions as a filter.",
        "The clinic operates as a charity registered in Ontario.",
        "The region comprises four districts.",
        "The programme encompasses four regions.",
        "That constitutes a breach of the agreement.",
        "He resides in Ottawa.",
        "The Mona Lisa resides in the Louvre.",
        "The board comprises seven members.",
    ],
)
def test_rejected_copula_verbs_stay_unflagged(text):
    """8/8 legitimate in the rejection probe. Pinned so a later round re-probes
    before adding them."""
    assert not find_regex_structures(text, load_regex_structures()), text


# --- BS-044 significance predicate -------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "It represents a shift in how the team works.",
        "The station marks a pivotal moment for the network.",
        "The rebuild represents the culmination of nine months.",
        "The award marks a milestone for the programme.",
        "The design embodies a commitment to plain language.",
    ],
)
def test_bs044_fires(text):
    assert _hits(text, "BS-044"), text


@pytest.mark.parametrize(
    "text",
    [
        "The graph represents the data from three sites.",
        "The lawyer represents the defendant.",
        "The symbol represents hydrogen.",
        "The line marks the boundary between the two lots.",
        "The pencil marks the paper.",
        "She represents the riding of Ottawa Centre.",
        "The map represents a scale of one to fifty thousand.",
        "The union represents four thousand workers.",
    ],
)
def test_bs044_concrete_object_does_not_fire(text):
    assert not _hits(text, "BS-044"), text


# --- BS-045 signposted conclusion --------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "In conclusion, the future depends on funding.",
        "To sum up, we have explored three themes.",
        "In summary, the evidence is thin.",
        "All in all, it worked.",
        "The work is done. To conclude, three things changed.",
    ],
)
def test_bs045_fires(text):
    assert _hits(text, "BS-045"), text


@pytest.mark.parametrize(
    "text",
    [
        "The jury reached a conclusion after two days.",
        "He wrote a summary of the meeting.",
        "She gave it in summary form.",
    ],
)
def test_bs045_does_not_fire(text):
    assert not _hits(text, "BS-045"), text


# --- BS-046 staccato negation ------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "Not a bug. Not a feature. A fundamental design flaw.",
        "Not the cause. Not the cure. Just the symptom.",
        "Not a strategy. Not a plan.",
    ],
)
def test_bs046_fires(text):
    assert _hits(text, "BS-046"), text


@pytest.mark.parametrize(
    "text",
    [
        "Not now. Not ever.",
        "Not today. He would wait.",
        "Not all of them agreed, but most did.",
        "Not bad. Not great. It was fine.",
        "He said no. She said nothing.",
    ],
)
def test_bs046_adverbial_emphasis_does_not_fire(text):
    """The determiner is the guard: ordinary human emphasis is adverbial."""
    assert not _hits(text, "BS-046"), text


# --- BS-047 analogy invitation -----------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "Think of it as a Swiss Army knife for your workflow.",
        "Think of it like a highway system for data.",
        "Think of this as the first draft.",
    ],
)
def test_bs047_fires(text):
    assert _hits(text, "BS-047"), text


@pytest.mark.parametrize(
    "text",
    ["I think of it as home.", "Think of the children.", "Do you think of it often?",
     '"Think of it as a favour," she said.'],
)
def test_bs047_does_not_fire(text):
    assert not _hits(text, "BS-047"), text


# --- BS-048 structure announcement -------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "Let's break this down step by step.",
        "Let's unpack what this really means.",
        "Let's dive into the details.",
        "Let's walk through the sequence.",
        "Let’s break it down.",
    ],
)
def test_bs048_fires(text):
    assert _hits(text, "BS-048"), text


@pytest.mark.parametrize(
    "text",
    [
        "Let's go.",
        "Let's be honest about the timeline.",
        "He let us break the seal.",
        "Let's explore the options together.",
        "Let's talk.",
    ],
)
def test_bs048_does_not_fire(text):
    """'Let's explore' was cut during the build as too close to ordinary
    collaborative writing, and 'Let's be honest' stays rejected from
    2026-07-25."""
    assert not _hits(text, "BS-048"), text


# --- BS-027 and BS-035 extensions --------------------------------------------
@pytest.mark.parametrize(
    "text",
    ["Imagine a world where every tool has a quiet intelligence.",
     "Picture a world where nobody files a form."],
)
def test_bs027_imperative_world_opener_fires(text):
    assert _hits(text, "BS-027"), text


@pytest.mark.parametrize("text", ["In a world of magic, anything goes.", "Imagine a world without borders."])
def test_bs027_extension_does_not_overreach(text):
    assert not _hits(text, "BS-027"), text


@pytest.mark.parametrize(
    "text",
    ["As we have seen, the walls are real.",
     "As we explored above, the pattern repeats.",
     "As we established earlier, the data is thin.",
     "As I have covered, the cost is fixed."],
)
def test_bs035_seen_extension_fires(text):
    assert _hits(text, "BS-035"), text


@pytest.mark.parametrize(
    "text",
    ["As we have seen the results, we can decide.",
     "We have seen worse.",
     "As we explored the cave, it grew colder.",
     "As we covered the roof, it began to rain."],
)
def test_bs035_extension_requires_a_cross_reference(text):
    assert not _hits(text, "BS-035"), text


# --- lexical additions --------------------------------------------------------
def test_lexical_additions_present():
    terms = load_flagged_terms()
    flat = set()

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            flat.add(o.lower())

    walk(terms)
    for w in ("profound", "renowned", "nestle", "diverse array", "natural beauty"):
        assert w in flat, w


# --- corpus and ReDoS ---------------------------------------------------------
@pytest.mark.parametrize("rule", NEW + ["BS-027", "BS-035"])
def test_no_false_positives_on_tier1_human_corpus(rule):
    """Tier 1 bar: zero findings on the modern matched-register corpus.

    All six survey rules are per-sentence shapes. On Tier 2, BS-043 and BS-045
    measure 0.2 per 10k and the rest 0.0 (see docs/RULE-HISTORY.md, 2026-09-18).
    """
    assert_tier1_clear(lambda text: _hits(text, rule), rule)


@pytest.mark.parametrize("rule", NEW)
def test_redos_safe(rule):
    s = next(s for s in load_regex_structures() if s["id"] == rule)
    for pathological in ("serves as a " * 20000, "Not a thing. " * 20000, "Let's break this down " * 10000):
        start = time.perf_counter()
        find_regex_structures(pathological, [s])
        assert (time.perf_counter() - start) < 1.0, rule
