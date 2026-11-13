"""The academic-research round: graded contrasts, chatbot residue, fiction
stock phrases, emotion inventories, corrective disclaimers and three closer
habits, plus the four-term lexicon addition.

Round: 2026-10-30. Spec:
docs/superpowers/specs/2026-10-30-research-round-academic-tells.md

Candidates came from a literature survey (Reinhart et al. PNAS 2025, Russell et
al. ACL 2025, Chakrabarty et al. CHI 2025, Antislop 2025, Graphite 2026,
Wikipedia:Signs of AI writing) and were probed on three human corpora and one
default-style Claude sample before any of them was written down. This file pins
the nine regex rules that survived (BS-056..BS-064), the BS-030 extension, the
hard negatives that narrowed them, and both standing corpus tiers with a
discriminating control in the same run. The two out-of-repo corpora (pre-2022
essays and pre-2022 Wikipedia) are reported in the spec, not tested here.
"""

import json
import pathlib
import re
import time

import pytest

from src.checker import run_checks
from src.checker.loader import load_budget_only_ids, load_flagged_terms, load_regex_structures
from src.checker.structures import find_regex_structures
from tests.support.fp_corpus import (
    assert_tier1_clear,
    rate_per_10k,
    tier2_available,
    tier2_files,
    tier2_sweep,
    tier2_within_bar,
)

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"
ROUND = ["BS-056", "BS-057", "BS-058", "BS-059", "BS-060", "BS-061", "BS-062", "BS-063", "BS-064"]


def _rule(rule_id: str):
    rules = [s for s in load_regex_structures() if s["id"] == rule_id]
    assert rules, f"{rule_id} is missing from banned_structures.json"
    return lambda text: find_regex_structures(text, rules)


RULES = {rule_id: _rule(rule_id) for rule_id in ROUND}
bs030 = _rule("BS-030")


def round_rules(text: str) -> list[dict]:
    return [hit for fn in RULES.values() for hit in fn(text)]


POSITIVES = {
    "BS-056": [
        "The role is less like a manager and more like a translator.",
        "It feels less like a meeting and more like a negotiation.",
        "Good onboarding is less like a lecture, more like an apprenticeship.",
    ],
    "BS-057": [
        "The job is less about speed and more about trust.",
        "Hiring is less about pedigree, more about range.",
    ],
    "BS-058": [
        "Certainly! Here is a revised version of your cover letter.",
        "Certainly, here's a revised version of the paragraph.",
        "As of my last knowledge cutoff, the bill had not passed.",
        "Absolutely! Below is a summary of the changes.",
        "As an AI language model, I cannot browse the web.",
        "Here's a polished version of the email:",
        "Would you like me to expand on any of these sections?",
        "Would you like me to adjust the tone?",
    ],
    "BS-059": [
        "Her voice was barely above a whisper.",
        "\"Stay,\" she said, barely above a whisper.",
        "She spoke, her voice trembling slightly.",
        "Her heart hammered against her ribs.",
        "His heart was pounding in his chest.",
        "The air was thick with the scent of rain.",
        "He watched her, eyes never leaving her face.",
        "The lamps were casting long shadows on the wall.",
        "A smile played on her lips.",
        "Elara opened the door.",
    ],
    "BS-060": [
        "She felt a mix of pride and sadness.",
        "It was a strange blend of relief and dread.",
        "A mixture of excitement and nervousness kept him awake.",
        "There was an uneasy mix of hope and fear in the room.",
        "They sat with the weight of the unspoken between them.",
    ],
    "BS-061": [
        "Claims about its floating should be treated as religious tradition rather than as archaeological explanation.",
        "The founder's early life is not widely documented.",
        "Based on the provided sources, the tower was completed in 1890.",
        "This detail does not appear in the provided sources.",
    ],
    "BS-062": [
        "The council approved the plan.\n\nAs the industry continues to evolve, one thing is clear: the future of cycling here looks bright.",
        "Sales rose in spring.\r\n\r\nOne thing is certain: the trend will hold.",
        "The bakery turns sixty this year.\n\nLooking ahead, the family hopes to open a second shop.",
        "As the field continues to mature, the future looks promising.",
    ],
    "BS-063": [
        "This distinction matters because teams often conflate the two.",
        "Knowing which type you have matters more than most beginners realize.",
        "It matters more than you'd think.",
        "## Why this matters\n\nThe deadline moved.",
    ],
    "BS-064": [
        "Gardening is as much about patience as technique.",
        "Leadership is as much a matter of listening as speaking.",
        "Good design was as much about restraint as it was about invention.",
        "It's as much about patience as technique.",
    ],
}

HARD_NEGATIVES = {
    "BS-056": [
        "He looks less like his father than his mother did.",
        "Nothing is less like home. More like a hotel, really.",
        "I'd like less coffee and more tea.",
        "It is more like a lecture and less like a talk.",
    ],
    "BS-058": [
        "Certainly! Certainly! we said.",
        "Of course! My dear physician!",
        "Sure! I'll be there at six.",
        "I hope this helps the committee decide.",
        "You're absolutely right, I missed that.",
        "I'd be happy to help with the move on Saturday.",
        "Let me know if you'd like me to send the deck.",
        "That's the great question.",
        "Great question, and I don't know the answer.",
        "Would you like me to come with you?",
        "Here is the revised schedule for Thursday.",
        # From the 2026-10-30 adversarial review: client email, Slack, bios.
        "Sure! Here's the Zoom link for tomorrow.",
        "Of course! Here are the photos from Saturday.",
        "Here's the updated draft of the lease with your edits.",
        "Here is the revised draft for Thursday's board pack.",
        "Would you like me to make any changes before it goes to print?",
        "As an AI researcher, I've watched this field change twice.",
        "She was hired as an AI ethics lead.",
        # The first draft fired on the sibling prompt's own "They read as an AI tell".
        "They read as an AI tell, and this prompt bans them outright.",
        "The essay was flagged as an AI text by the detector.",
    ],
    "BS-059": [
        "Her voice rose above the noise.",
        "The air was thick with smoke.",
        "He couldn't shake the cold.",
        "The trees cast shadows on the lawn.",
        "She had a smile on her lips.",
        "He took a deep breath and went in.",
        "I'd rather do something else entirely.",
        "She has a sense of humour.",
        "His heart was in the right place.",
        # From the 2026-10-30 adversarial review: memoir, bug reports, news, condolences, criticism.
        "Pauline Kael hated it.",
        "I woke at 3 a.m. with my heart pounding in my chest.",
        "Since the update, my voice was barely audible on calls.",
        "The air was thick with the smell of tear gas.",
        "We feel a profound sense of loss at Margaret's passing.",
        "I couldn't shake the feeling I'd left the stove on.",
    ],
    "BS-060": [
        "Add a mix of flour and sugar.",
        "It is a blend of tea and spices.",
        "She felt a mix of pride.",
        "The weight of the evidence was against him.",
        "It was an unspoken rule.",
        "I felt a sense of urgency about the deadline.",
    ],
    "BS-061": [
        "It should be read as a whole rather than in parts.",
        "Treat the figure as an estimate rather than a count.",
        "The ruling does not establish that the park was contaminated.",
        "The species is widely documented in the region.",
        "Based on the survey, we moved the stop.",
        # From the 2026-10-30 adversarial review: legal, academic, police and historiography boilerplate.
        "The provision should be read as a limitation on agency power rather than as a grant of authority.",
        "These results should be interpreted as exploratory rather than as confirmatory.",
        "Based on the available information, police believe the fire was accidental.",
        "There is no mention of him in the available sources before 1650.",
    ],
    "BS-062": [
        "Looking ahead, the council plans a vote.\n\nThe vote is in March.",
        "Only time will tell, she said.\n\nThen she left for the station.",
        "As the town continues to grow, traffic gets worse.\n\nThe new bypass opens in June.",
        "The future of the project is uncertain.",
        # From the 2026-10-30 adversarial review.
        "Looking ahead, x.\r\n\r\nThe next paragraph has content.",
        "Looking ahead, phase two opens on 3 March.",
        "Looking ahead, the vote is in March.",
        # From the terse-register set (2026-11-09): a weekday or a relative
        # day is as concrete as a month name.
        "Looking ahead, the forecast calls for rain through Thursday.",
        "Looking ahead, the site is down for maintenance tonight.",
        "Looking ahead, tomorrow's session starts at nine.",
        "Looking ahead, the trails close this weekend.",
        "As the plant continues to grow, move it to a larger pot.",
        "It remains to be seen whether the Senate will take up the bill.",
        "\"Only time will tell,\" the coach said.",
    ],
    "BS-063": [
        "It matters very little now.",
        "What matters is the date.",
        "If you build something users love, it may matter more than outsiders think.",
        "That matters to me.",
        "Nothing matters more than sleep.",
        "Grey matters in neuroscience.",
        "The order matters here: auth middleware must run before the router.",
    ],
    "BS-064": [
        "I ate as much as I could.",
        "It costs as much as a car.",
        "She earns twice as much as he does.",
        "It was as much a surprise to me.",
        "The film is as much about the city as it is about the people who leave it.\n\nIt opens Friday.",
    ],
}


@pytest.mark.parametrize("rule_id,text", [(r, t) for r, ts in POSITIVES.items() for t in ts])
def test_round_rules_fire_on_constructed_tells(rule_id, text):
    assert RULES[rule_id](text), (rule_id, text)


@pytest.mark.parametrize("rule_id,text", [(r, t) for r, ts in HARD_NEGATIVES.items() for t in ts])
def test_round_rules_decline_hard_negatives(rule_id, text):
    assert not RULES[rule_id](text), (rule_id, text)


@pytest.mark.parametrize("text", [t for ts in HARD_NEGATIVES.values() for t in ts])
def test_no_round_rule_fires_on_any_hard_negative(text):
    """Cross-check: a hard negative written for one rule must not be caught by
    a sibling either, or the narrowing just moved the false positive."""
    assert not round_rules(text), text


# ---------------------------------------------------------------------------
# BS-057 is budget-only: one 'less about ... more about' is ordinary writing
# ---------------------------------------------------------------------------

ONE_ABOUT = "I care less about the price and more about the fit."
TWO_ABOUT = ONE_ABOUT + " Hiring is less about pedigree and more about range."


def test_bs057_is_budget_only():
    assert "BS-057" in load_budget_only_ids()
    must = run_checks(ONE_ABOUT, "prose")["must_clear"]
    assert not [m for m in must if m.get("id") == "BS-057"]


def test_bs057_reports_the_repeat_once_with_both_excerpts():
    must = run_checks(TWO_ABOUT, "prose")["must_clear"]
    hits = [m for m in must if m.get("id") == "BS-057"]
    assert len(hits) == 1 and hits[0]["type"] == "document_budget" and hits[0]["count"] == 2
    assert len(hits[0]["excerpts"]) == 2


def test_bs056_is_not_budget_only():
    """Control: the 'like' form fired nowhere in human prose, so a single
    instance is reported on its own."""
    must = run_checks(POSITIVES["BS-056"][0], "prose")["must_clear"]
    assert [m for m in must if m.get("id") == "BS-056" and m["type"] == "banned_structure"]


# ---------------------------------------------------------------------------
# BS-062 is scoped to the last paragraph by a lookahead
# ---------------------------------------------------------------------------


def test_bs062_fires_only_in_the_last_paragraph():
    body = "Looking ahead, the council plans a vote.\n\nThe vote is in March."
    assert not RULES["BS-062"](body)
    assert RULES["BS-062"]("The vote is in March.\n\nLooking ahead, the council plans a second vote.")


def test_bs062_ignores_trailing_whitespace_after_the_last_paragraph():
    assert RULES["BS-062"]("Sales rose.\n\nOne thing is clear: buses.\n\n   \n")
    assert RULES["BS-062"]("Sales rose.\r\n\r\nOne thing is clear: buses.\r\n\r\n")


# ---------------------------------------------------------------------------
# BS-030 extension: "If this sounds familiar, take heart."
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "If this sounds familiar, take heart. Most problems are easy to fix.",
        "If any of this sounds familiar, you're not alone.",
        "Slow builds? If that sounds familiar, don't worry.",
        "Sound familiar? You're not alone.",
        "If this sounds familiar to you, take heart.",
    ],
)
def test_bs030_catches_the_familiar_reassurance_opener(text):
    assert bs030(text), text


@pytest.mark.parametrize(
    "text",
    [
        "If this sounds familiar, it's because I wrote about it last week.",
        "If that sounds familiar, you may have read the first report.",
        "If you've ever been to Paris, you know the light.",
    ],
)
def test_bs030_extension_declines_a_callback(text):
    assert not bs030(text), text


# ---------------------------------------------------------------------------
# Lexicon additions
# ---------------------------------------------------------------------------


def test_the_four_new_terms_are_flagged_at_low_severity():
    terms = {t["term"]: t for t in load_flagged_terms()}
    for word in ("camaraderie", "unease", "palpable", "unspoken"):
        assert terms[word]["severity"] == "low", word


def test_uneasiness_and_amidst_are_not_flagged():
    """'uneasiness' is Victorian vocabulary and 'amidst' measured 2.1 per 10k on
    Tier 2 and 0 in the AI sample, so neither was added."""
    findings = run_checks("It gave me great uneasiness, amidst the noise.", "prose")["must_clear"]
    assert not [f for f in findings if f.get("type") == "flagged_term"]


# ---------------------------------------------------------------------------
# Corpus tiers, with a discriminating control in the same run
# ---------------------------------------------------------------------------


def test_tier1_stays_clear_of_the_round():
    for rule_id, fn in RULES.items():
        assert_tier1_clear(fn, rule_id)


# A loose version of each frame. The scoped rules' zero is reportable only if
# these fire in the same run. Measured 2026-10-30 on Tier 2: 'less ... more' 17,
# 'voice' over 1,000, 'rather than' 40, 'continues to' 11, 'matters' 86,
# 'as much' 168.
_CONTROLS = {
    "BS-056": re.compile(r"\bless\b[^.?!;:\n]{1,60}?\bmore\b", re.IGNORECASE),
    "BS-059": re.compile(r"\bvoice\b", re.IGNORECASE),
    "BS-061": re.compile(r"\brather\s+than\b", re.IGNORECASE),
    "BS-062": re.compile(r"\bcontinues?\s+to\b", re.IGNORECASE),
    "BS-063": re.compile(r"\bmatters\b", re.IGNORECASE),
    "BS-064": re.compile(r"\bas\s+much\b", re.IGNORECASE),
}
# Fresh per round: the sentinel a round uses gets written into its own spec.
_SENTINEL = re.compile(r"\bwhelkbrine\s+obquaver\b", re.IGNORECASE)


def _tier2_count(pattern: re.Pattern) -> int:
    return sum(len(pattern.findall(p.read_text(encoding="utf-8"))) for p in tier2_files())


@pytest.mark.skipif(not tier2_available(), reason="Tier 2 corpus not fetched")
def test_tier2_rate_with_controls_that_fire():
    for rule_id, pattern in _CONTROLS.items():
        assert _tier2_count(pattern) >= 10, f"{rule_id} control is blind; the zero below means nothing"
    assert _tier2_count(_SENTINEL) == 0

    total, rate, per_work = tier2_sweep(round_rules)
    assert tier2_within_bar(total), (total, rate, per_work)
    # Measured 2026-10-30: 0 across all nine rules, 0.0 per 10k.
    assert total == 0, per_work
    assert rate_per_10k(total) == 0.0


# ---------------------------------------------------------------------------
# Data wiring
# ---------------------------------------------------------------------------


def _entries() -> dict[str, dict]:
    return {s["id"]: s for s in json.loads((DATA / "banned_structures.json").read_text())["structures"]}


def test_round_rules_are_checklist_never_hard():
    entries = _entries()
    for rule_id in ROUND:
        assert entries[rule_id]["gate"] == "checklist", rule_id
        assert entries[rule_id]["detection"]["method"] == "regex", rule_id
        assert "2026-10-30" in entries[rule_id]["research_basis"], rule_id
    assert entries["BS-057"]["document_budget"] == 1 and entries["BS-057"]["budget_only"] is True


def test_patterns_avoid_scoped_inline_flags():
    """The browser port translates each pattern to a JS RegExp, which has no
    scoped (?-i:...) or (?m:...) groups. Keep the round's patterns portable."""
    entries = _entries()
    for rule_id in ROUND + ["BS-030"]:
        pattern = entries[rule_id]["detection"]["pattern"]
        assert "(?-i:" not in pattern and "(?m:" not in pattern and "(?i:" not in pattern, rule_id


def test_round_examples_exist_and_fire():
    aps = {a["id"]: a for a in json.loads((DATA / "anti_patterns.json").read_text())["patterns"]}
    entries = _entries()
    for rule_id in ROUND:
        for ap in entries[rule_id]["source_examples"]:
            assert ap in aps, (rule_id, ap)
    for ap_id, rule_ids in {
        "AP-065": ["BS-056"],
        "AP-066": ["BS-062", "BS-063", "BS-064"],
        "AP-067": ["BS-059", "BS-060"],
        "AP-068": ["BS-058", "BS-061"],
    }.items():
        before = aps[ap_id]["before"]
        for rule_id in rule_ids:
            assert RULES[rule_id](before), (ap_id, rule_id)
        assert not round_rules(aps[ap_id]["after"]), ap_id


def test_caveat_records_the_default_sample_finding():
    caveats = {c["id"]: c for c in json.loads((DATA / "caveats.json").read_text())["core_caveats"]}
    entry = caveats["default_model_prose_mostly_passes"]
    # The measurement is maintainer history; the served text keeps the advice.
    assert "2026-10-30" in entry["history"] and "21 of the 32" in entry["history"]
    assert "self-review rubric" in entry["explanation"]


def test_the_corrected_claims_stay_corrected():
    """Three statements in the data contradicted the literature or this
    server's own detectors until 2026-10-30. Pin the corrections."""
    lex = json.loads((DATA / "lexical_patterns.json").read_text())
    adverbs = lex["adverb_patterns"]["human_adverbs_to_keep"]
    for word in ("quietly", "actually", "honestly"):
        assert word not in adverbs, word
    assert "Human text scores higher" not in json.dumps(lex["vocabulary_diversity"])
    structural = (DATA / "structural_patterns.json").read_text()
    assert "AI text uses passive voice at a steady rate" not in structural


# ---------------------------------------------------------------------------
# ReDoS
# ---------------------------------------------------------------------------

PATHOLOGICAL = [
    "less " + "like a " * 40000 + "x",
    "a" + " aa" * 70000 + "x",
    "should be treated as " + "word " * 40000,
    "x\n\n" * 50000 + "only time will tell",
    "as much about " * 20000,
    "matters more than " + "people " * 30000,
    "#" * 100000 + " why",
    # From the 2026-10-30 review: many candidate phrases, each scanning to the end.
    "One thing is clear: x. " * 4400,
    "One thing is clear: x.\n\n" * 4300,
    "It is as much about a as b. " * 3600,
    # From the 2026-11-09 terse-register round: BS-062's date guard scanned to
    # the end of the sentence and backtracked through every month and weekday
    # name per candidate. 9.6 s at the 100k cap on main before the bound.
    "Looking ahead, " * 6600,
    ". Looking ahead, " * 5800,
]


@pytest.mark.parametrize("text", PATHOLOGICAL)
def test_round_rules_are_redos_safe(text):
    assert len(text) >= 95000 or text.count("\n") >= 100000
    start = time.perf_counter()
    round_rules(text)
    bs030(text)
    assert time.perf_counter() - start < 2.0
