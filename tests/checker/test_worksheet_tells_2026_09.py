"""The worksheet false negatives: time nouns as agents, the clipped retention
verdict, the deictic stance closer and the "[time] back" refrain.

Round: 2026-09-29. Spec:
docs/superpowers/specs/2026-09-29-worksheet-false-negatives.md

A B2 student exemplar written in worksheet cells came back prohibitions_clear
with no structural findings while a human reviewer flagged six phrases. This
file pins the four regex rules that close the mechanizable part of that gap
(BS-052..BS-055), the budget-only reporting BS-055 needs, and both corpus tiers
with a discriminating control in the same run.
"""

import json
import pathlib
import re

import pytest

from src.checker import run_checks
from src.checker.loader import load_budget_only_ids, load_regex_structures
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


def _rule(rule_id: str):
    rules = [s for s in load_regex_structures() if s["id"] == rule_id]
    assert rules, f"{rule_id} is missing from banned_structures.json"
    return lambda text: find_regex_structures(text, rules)


bs052 = _rule("BS-052")
bs053 = _rule("BS-053")
bs054 = _rule("BS-054")
bs055 = _rule("BS-055")


def round_rules(text: str) -> list[dict]:
    return bs052(text) + bs053(text) + bs054(text) + bs055(text)


# ---------------------------------------------------------------------------
# BS-052 time_noun_as_agent
# ---------------------------------------------------------------------------

# The first three are verbatim from the reviewed draft.
BS052_ATTESTED = [
    "Co-op hours were 9 to 5, so the Fridays survived.",
    "Busy season eats the Fridays.",
    "Billiards survives final year.",
    "Work does not get to claim them.",
]
BS052_CONSTRUCTED = [
    "The semester swallowed my evenings.",
    "Exam season kills the evenings.",
    "Hockey season ate our Saturdays.",
    "The tutoring survives the semester.",
    "- Busy season eats the Fridays.",
]
BS052_HARD_NEGATIVES = [
    "The winter killed the roses.",
    "Mondays kill me.",
    "Work ate my whole weekend.",
    "Friday's storm killed the power.",
    "The dog ate the Friday paper.",
    "The terms claimed by the vendor were vague.",
    "Evenings steal up on you in October.",
    "Sunday's paper claimed the mayor lied.",
    "Schedule survives restarts because it is stored on disk.",
    "The evening died away into night.",
    "Tuesdays claimed by the club are marked in red.",
    "Most seedlings survive the winter.",
    "The firm survived the recession.",
    # From the 2026-09-29 review: human subjects, compounds, headings, news.
    "I barely survived the semester.",
    "We survived another busy season.",
    "I survived final year.",
    "He survives the semester somehow.",
    "People who work don't get to have a say.",
    "Kids at school don't get to keep their phones.",
    "Anyone at work doesn't get to take my spot.",
    "Weekend eats: five brunch spots",
    "Weekend steals start Friday.",
    "Saturday claims are processed on Monday.",
    "Friday die-hards packed the bar.",
    "The weekend claimed two lives on Highway 1.",
]


@pytest.mark.parametrize("text", BS052_ATTESTED + BS052_CONSTRUCTED)
def test_bs052_fires_on_time_nouns_as_agents(text):
    assert bs052(text), text


@pytest.mark.parametrize("text", BS052_HARD_NEGATIVES)
def test_bs052_declines_literal_and_idiomatic_uses(text):
    assert not bs052(text), text


def test_bs052_passes_the_accepted_rewrites():
    for text in (
        "My summer co-op term ends at 5 most days, so I still make it to billiards on Fridays.",
        "No billiards from January to April.",
        "I play billiards every second Friday through final year.",
    ):
        assert not round_rules(text), text


# ---------------------------------------------------------------------------
# BS-053 clipped_retention_verdict
# ---------------------------------------------------------------------------

BS053_ATTESTED = [
    "I dropped two things. The Scouts books and the tutoring stay.",
    "Tutoring stays.",
]
BS053_CONSTRUCTED = [
    "The Friday class stays.",
    "| Tutoring stays. |",
    "Cut the gym. Swimming goes.",
    "- Tutoring stays.",
    "Done.  Tutoring stays.",
]
BS053_HARD_NEGATIVES = [
    "The car stays in the garage.",
    "He stays.",
    "She remains.",
    "It stays.",
    "Nothing remains.",
    "As the saying goes.",
    "So it goes.",
    "Anything goes.",
    "There it goes.",
    "Mr. Skimpole prolonged his stay.",
    "As such I shall remain.",
    "Then she let it remain.",
    "Tell him to stay.",
    "The house was sold but the garden remains.",
    "Only the chapel remains.",
    # From the 2026-09-29 review. 'remains' is out of scope entirely, and the
    # quantifier, title and all-caps cases are declined.
    "Questions remain.",
    "Doubts remain.",
    "The chapel remains.",
    "Piano remains.",
    "No one stays.",
    "Few remain.",
    "Others stay.",
    "Please stay.",
    "NOTHING REMAINS.",
    "HE STAYS.",
    "Mr. Darcy stays.",
]

# Accepted residual, pinned so it is a decision rather than a surprise.
BS053_KNOWN_RESIDUAL = "Fine. The dog stays."


@pytest.mark.parametrize("text", BS053_ATTESTED + BS053_CONSTRUCTED)
def test_bs053_fires_on_clipped_verdicts(text):
    assert bs053(text), text


@pytest.mark.parametrize("text", BS053_HARD_NEGATIVES)
def test_bs053_declines_literal_and_pronoun_uses(text):
    assert not bs053(text), text


def test_bs053_known_residual_still_fires():
    assert bs053(BS053_KNOWN_RESIDUAL)


def test_bs053_passes_the_accepted_rewrite():
    assert not round_rules("I am keeping the Scouts books and the tutoring.")


def test_bs053_is_budgeted_so_a_repeat_is_reported():
    text = "Tutoring stays. I cut the gym. Piano stays. The rest goes to the weekend."
    budget = [
        m for m in run_checks(text, "prose")["must_clear"]
        if m.get("type") == "document_budget" and m["id"] == "BS-053"
    ]
    assert len(budget) == 1 and budget[0]["count"] == 2


# ---------------------------------------------------------------------------
# BS-054 deictic_stance_closer
# ---------------------------------------------------------------------------

BS054_POSITIVES = [
    "Seven to eight hours of sleep, and I want to keep it there.",
    "I sleep 8 hours now and I'd like to keep it that way.",
    "My average is 85 and I want to keep it there.",
]
BS054_HARD_NEGATIVES = [
    "I want to keep it simple.",
    "We want to keep it there until Tuesday, then move it.",
    "I want to keep it.",
    "I want to keep them apart.",
    # From the 2026-09-29 review: no number to point back at, or 'up'.
    "I'd like to keep it that way.",
    "I've been running daily and I want to keep it up.",
    "The spare key is under the mat and I want to keep it there.",
    "The kids are finally in bed; I plan to keep them there.",
    "My grades are fine and I want to keep it that way.",
]


@pytest.mark.parametrize("text", BS054_POSITIVES)
def test_bs054_fires_on_the_clause_final_stance_closer(text):
    assert bs054(text), text


@pytest.mark.parametrize("text", BS054_HARD_NEGATIVES)
def test_bs054_declines_a_closer_that_carries_content(text):
    assert not bs054(text), text


# ---------------------------------------------------------------------------
# BS-055 time_back_refrain: budget-only
# ---------------------------------------------------------------------------

TWO_REFRAINS = "I get my Fridays back in May. By then I have my evenings back too."
ONE_REFRAIN = "I get my Fridays back in May."


def test_bs055_matches_both_attested_forms():
    assert len(bs055(TWO_REFRAINS)) == 2
    assert not bs055("I got my money back.")
    assert not bs055("She had her back to the wall.")


def test_bs055_is_budget_only_so_one_use_is_silent():
    """One 'get my Fridays back' is ordinary writing; the refrain is the tell.
    The instance findings are dropped and only the overrun is reported."""
    assert "BS-055" in load_budget_only_ids()
    must = run_checks(ONE_REFRAIN, "prose")["must_clear"]
    assert not [m for m in must if m.get("id") == "BS-055"]


def test_bs055_reports_the_overrun_once():
    must = run_checks(TWO_REFRAINS, "prose")["must_clear"]
    hits = [m for m in must if m.get("id") == "BS-055"]
    assert len(hits) == 1
    assert hits[0]["type"] == "document_budget" and hits[0]["count"] == 2
    excerpts = hits[0]["excerpts"]
    assert len(excerpts) == 2
    assert "Fridays back" in excerpts[0] and "evenings back" in excerpts[1]


def test_budget_only_never_hides_an_unbudgeted_rule():
    """Control: BS-011 carries a budget but is not budget-only, so its single
    instance must still be reported individually."""
    must = run_checks("The work is judgement, not process.", "prose")["must_clear"]
    assert [m for m in must if m.get("id") == "BS-011" and m["type"] == "banned_structure"]
    assert "BS-011" not in load_budget_only_ids()


# ---------------------------------------------------------------------------
# The reviewed draft, end to end
# ---------------------------------------------------------------------------

REVIEWED_CELLS = (
    "Co-op hours were 9 to 5, so the Fridays survived.\n\n"
    "Busy season eats the Fridays.\n\n"
    "Billiards survives final year.\n\n"
    "The Scouts books and the tutoring stay.\n\n"
    "Seven to eight hours of sleep, and I want to keep it there."
)


def test_the_reviewed_draft_now_surfaces_each_flagged_phrase():
    must = run_checks(REVIEWED_CELLS, "prose")["must_clear"]
    ids = [m.get("id") for m in must if m.get("type") == "banned_structure"]
    assert ids.count("BS-052") == 3
    assert ids.count("BS-053") == 1
    assert ids.count("BS-054") == 1


# ---------------------------------------------------------------------------
# Corpus tiers, with a discriminating control in the same run
# ---------------------------------------------------------------------------


def test_tier1_stays_clear_of_the_round():
    for rule_id, fn in (("BS-052", bs052), ("BS-053", bs053), ("BS-054", bs054), ("BS-055", bs055)):
        assert_tier1_clear(fn, rule_id)


# A loose version of each frame, with the guards removed. A zero from the
# scoped rule is reportable only if its loose control fires in the same run.
# Measured 2026-09-29: only the retention verdict has one (18 firings: "his
# stay.", "shall remain.", "difficulty remains."). The time-noun agent, the
# stance closer and the refrain fire 0, 1 and 2 times even loose, so their
# Tier 2 zero is blind and they ship at confidence "low" on constructed
# evidence (caveats.worksheet_cells_hide_semantic_tells).
_VERDICT_CONTROL = re.compile(r"\b\w+\s+(?:stays|stay|remains|remain)\.", re.IGNORECASE)
_BLIND_CONTROLS = {
    "BS-052": re.compile(
        r"\b(?:time|days?|nights?|evenings?|mornings?|winter|summer|years?|seasons?|weeks?|hours?|months?)"
        r"\s+(?:had\s+|has\s+|would\s+|will\s+)?(?:eat|ate|eats|eaten|devour\w*|kill\w*|steal\w*|stole|claim\w*|swallow\w*|surviv\w*)\b",
        re.IGNORECASE,
    ),
    "BS-054": re.compile(r"\b(?:I|we)\s+\w+\s+to\s+keep\s+(?:it|them)\b", re.IGNORECASE),
    "BS-055": re.compile(
        r"\b(?:get|gets|got|getting|have|has|had|having)\s+(?:my|our|your|his|her|their)\s+\w+\s+back\b",
        re.IGNORECASE,
    ),
}


def _tier2_count(pattern: re.Pattern) -> int:
    return sum(len(pattern.findall(p.read_text(encoding="utf-8"))) for p in tier2_files())


@pytest.mark.skipif(not tier2_available(), reason="Tier 2 corpus not fetched")
def test_tier2_rate_with_a_control_that_fires():
    control = _tier2_count(_VERDICT_CONTROL)
    assert control >= 10, f"verdict control fired only {control} times; the zero below is blind"

    total, rate, per_work = tier2_sweep(round_rules)
    assert tier2_within_bar(total), (total, rate, per_work)
    assert total == 0, per_work
    assert rate_per_10k(total) == 0.0


@pytest.mark.skipif(not tier2_available(), reason="Tier 2 corpus not fetched")
def test_the_blind_zeros_are_still_blind():
    """Pins the reason three rules ship at low confidence. If a future corpus
    makes these controls fire, re-measure the rules and revisit the confidence."""
    for rule_id, pattern in _BLIND_CONTROLS.items():
        assert _tier2_count(pattern) <= 5, rule_id


# ---------------------------------------------------------------------------
# Data wiring
# ---------------------------------------------------------------------------


def test_rules_are_checklist_never_hard():
    entries = {s["id"]: s for s in json.loads((DATA / "banned_structures.json").read_text())["structures"]}
    for rule_id in ("BS-052", "BS-053", "BS-054", "BS-055"):
        assert entries[rule_id]["gate"] == "checklist"
    assert entries["BS-053"]["detection"]["confidence"] == "medium"
    for rule_id in ("BS-052", "BS-054", "BS-055"):
        assert entries[rule_id]["detection"]["confidence"] == "low", rule_id
    assert entries["BS-053"]["document_budget"] == 1
    assert entries["BS-055"]["document_budget"] == 1
    assert entries["BS-055"]["budget_only"] is True


def test_caveat_records_the_worksheet_finding_with_its_date():
    caveats = {c["id"]: c for c in json.loads((DATA / "caveats.json").read_text())["core_caveats"]}
    entry = caveats["worksheet_cells_hide_semantic_tells"]
    assert "2026-09-29" in entry["explanation"]
    assert "BS-052" in entry["explanation"]


# ---------------------------------------------------------------------------
# content_type="label": the caller opts out of the length metrics
# ---------------------------------------------------------------------------

FLAT_CELLS = (
    "I sleep seven hours. I study in the library. I work on Fridays. "
    "I play billiards with friends. I tutor one student. I read on the bus."
)


def test_prose_still_flags_flat_worksheet_cells():
    types = {m.get("type") for m in run_checks(FLAT_CELLS, "prose")["must_clear"]}
    assert "burstiness" in types


@pytest.mark.parametrize("content_type", ["label", "notes", "LABEL"])
def test_label_content_type_reports_metrics_without_a_finding(content_type):
    report = run_checks(FLAT_CELLS, content_type)
    types = {m.get("type") for m in report["must_clear"]}
    assert "burstiness" not in types and "segment_uniformity" not in types
    # Still measured, so the number is visible, but marked as not applying.
    assert report["metrics"]["length_stdev"] < 6.0
    assert report["metrics"]["length_metrics_apply"] is False


SECTIONED_FLAT = "\n\n".join([FLAT_CELLS] * 4)


def test_label_content_type_also_silences_segment_uniformity():
    """FLAT_CELLS is one paragraph, below segment_uniformity's three-section
    minimum, so this needs its own multi-section input to be able to fail."""
    prose = {m.get("type") for m in run_checks(SECTIONED_FLAT, "prose")["must_clear"]}
    assert "segment_uniformity" in prose
    label = run_checks(SECTIONED_FLAT, "label")
    assert "segment_uniformity" not in {m.get("type") for m in label["must_clear"]}
    assert label["metrics"]["segment_variation"]["uniformity_flag"] is False
    assert label["metrics"]["burstiness_flag"] is False


def test_label_content_type_keeps_every_other_layer():
    """Control in the same run: opting out of the metrics must not quiet the
    structures, which stay meaningful at any length."""
    must = run_checks("Tutoring stays. " + FLAT_CELLS, "label")["must_clear"]
    assert [m for m in must if m.get("id") == "BS-053"]


# ---------------------------------------------------------------------------
# ReDoS
# ---------------------------------------------------------------------------

PATHOLOGICAL = [
    "A" + " aa" * 70000 + "x",
    "so the " + "fridays " * 30000,
    "Seven " + "I want to keep " * 15000,
    "| " * 100000,
    "Tutoring " * 40000 + "stays.",
    "- " + "Busy season " * 20000,
]


@pytest.mark.parametrize("rule_id", ["BS-052", "BS-053", "BS-054", "BS-055"])
def test_redos_safe_on_pathological_input(rule_id):
    import time

    fn = {"BS-052": bs052, "BS-053": bs053, "BS-054": bs054, "BS-055": bs055}[rule_id]
    assert max(len(p) for p in PATHOLOGICAL) >= 200_000
    start = time.perf_counter()
    for text in PATHOLOGICAL:
        fn(text)
    assert time.perf_counter() - start < 2.0, rule_id


def test_must_be_zero_sentinel_on_both_tiers():
    """A fresh sentinel for this round (the modern control warns that a reused
    one gets written into a spec and then fires). Never write it in prose."""
    sentinel = re.compile("q" + "xv" + "worksheetz")
    from tests.support.fp_corpus import tier1_files

    files = tier1_files() + (tier2_files() if tier2_available() else [])
    assert sum(len(sentinel.findall(p.read_text(encoding="utf-8"))) for p in files) == 0
