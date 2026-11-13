"""PR 1 fix wave: pins for the whole-branch review of the repair round.

The removals sit in `REMOVED_PHRASES` in test_guide_consistency.py. This module
pins what a removal list cannot: guidance that stays but is now conditioned on
the source (absolute_rules AR-001), rewritten anti-pattern afters, the em-dash
guard over served prose, and cross-references that must name the right entry.
"""

import re

from src.checker.loader import load_flagged_terms
from src.storage.json_store import load_json
from tests.data.test_guide_consistency import asks_for_beats, fires, served_texts

EM_DASH = "—"

# Naming the character is how the guide forbids it ("Never use em-dashes (—).").
_NAMES_THE_CHARACTER = f"({EM_DASH})"

_ANAPHORA_CAVEAT = next(
    i for i, c in enumerate(load_json("caveats.json")["core_caveats"])
    if c["id"] == "rhetorical_figures_defeat_shape_detection"
)

# Served strings that still carry an em-dash and move in PR 2: the rubric
# (self_review, Task 10) and the anaphora caveat, which leaves served text.
_EM_DASH_DEFERRED_TO_PR2 = (
    "self_review[",
    f".caveats.core_caveats[{_ANAPHORA_CAVEAT}].",
)


def _ap(ap_id: str) -> dict:
    return next(p for p in load_json("anti_patterns.json")["patterns"] if p["id"] == ap_id)


def _strings_containing(needle: str) -> list[tuple[str, str]]:
    return [(p, s) for p, s in served_texts() if needle in s]


# ---------------------------------------------------------------------------
# Em-dash guard
# ---------------------------------------------------------------------------


def em_dash_offenders(texts: list[tuple[str, str]]) -> list[str]:
    """Paths of served strings with an em-dash that is not in a `before`
    field, not the "(—)" naming form, and not deferred to PR 2."""
    offenders = []
    for path, text in texts:
        if path.endswith(".before"):
            continue
        if any(marker in path for marker in _EM_DASH_DEFERRED_TO_PR2):
            continue
        if EM_DASH in text.replace(_NAMES_THE_CHARACTER, ""):
            offenders.append(path)
    return offenders


def test_em_dash_guard_control():
    assert em_dash_offenders([("guide[x].a.explanation", f"One {EM_DASH} two.")])
    assert not em_dash_offenders([("guide[x].a.before", f"One {EM_DASH} two.")])
    assert not em_dash_offenders([("guide[x].a.title", f"Never use em-dashes ({EM_DASH}).")])
    assert not em_dash_offenders([("self_review[3]", f"One {EM_DASH} two.")])


def test_no_em_dash_in_served_prose():
    assert em_dash_offenders(served_texts()) == []


# ---------------------------------------------------------------------------
# Guidance that stays, conditioned on the source (AR-001)
# ---------------------------------------------------------------------------

# Each needle is an example that survives the fix wave; every served string
# that carries it must say the move depends on the source.
CONDITIONED_ON_SOURCE = (
    "I haven't tested it at scale",
    "I'm not sure this holds for every case",
    "This is the most reliable method",
    "usability issues",
    "then blunt",
    "rephrase at least one instance",
)


def test_conditioned_guidance_names_the_source():
    for needle in CONDITIONED_ON_SOURCE:
        found = _strings_containing(needle)
        assert found, f"control: {needle!r} is no longer served"
        for path, text in found:
            assert "source" in text, (needle, path)


def test_rubric_items_4_and_8_keep_texture_to_the_job_and_the_source():
    items = [str(i) for i in load_json("self_review.json")["self_review"]["items"]]
    item4 = next(i for i in items if i.startswith("Section-to-section variation"))
    item8 = next(i for i in items if i.startswith("Excessive coherence"))
    assert "do not make sections differ for contrast" in item4
    assert "add none it lacks (AR-001)" in item8


def test_anti_pattern_usage_says_after_specifics_stand_for_source_facts():
    usage = load_json("anti_patterns.json")["meta"]["usage"]
    assert "marked placeholder (absolute_rules AR-001)" in usage


def test_confidence_rule_keeps_the_source_hedges():
    rules = load_json("discourse_cohesion.json")["modal_and_epistemic_markers"]["rules"]
    text = " ".join(f"{r['rule']} {r['guidance']}" for r in rules)
    assert "do not add or drop a hedge" in text
    stop = load_json("foundation.json")["application_protocol"]["phases"]
    phase4 = next(p for p in stop if p["phase"] == 4)["stop_condition"]
    assert "hedge" in phase4 and "unevenly" not in phase4


def test_qualifier_rule_swaps_for_the_same_limit():
    rule = load_json("lexical_patterns.json")["flagged_qualifiers"]["rule"]
    assert "same limit" in rule


def test_degree_adverbs_follow_the_source():
    rules = load_json("lexical_patterns.json")["adverb_patterns"]["rules"]
    first = rules[0]
    assert "source" in first["guidance"], first
    assert "AR-001" in first["guidance"], first


# ---------------------------------------------------------------------------
# Anti-pattern afters and cross-references
# ---------------------------------------------------------------------------


def test_ap016_after_keeps_may_vary():
    assert "may vary" in _ap("AP-016")["after"]


def test_ap019_and_ap052_afters_do_not_pivot_on_a_colon():
    for ap_id in ("AP-019", "AP-052"):
        assert ":" not in _ap(ap_id)["after"], ap_id


def test_ap037_after_uses_placeholders_not_invented_specifics():
    after = _ap("AP-037")["after"]
    assert not re.search(r"\d", after), after
    assert "[year]" in after and "[authors]" in after
    assert fires(after) == []


def test_ap002_explanation_matches_ar003_on_pivots():
    e = _ap("AP-002")["explanation"]
    assert "a comma only before a tail that is not a clause" in e


def test_cross_references_name_the_right_entries():
    assert "AP-029" in _ap("AP-052")["explanation"]
    assert "AP-021" not in _ap("AP-052")["explanation"]
    assert "Sarah" not in _ap("AP-027")["explanation"]
    assert "Teodora" in _ap("AP-027")["explanation"]


def test_copula_rule_offers_no_short_abstract_verdict():
    rules = load_json("structural_patterns.json")
    text = str(rules)
    assert "'This is a significant development'" not in text


# ---------------------------------------------------------------------------
# Fragments, non-uniformity, the lexicon, the protocol wording
# ---------------------------------------------------------------------------


def test_ar003_names_the_fiction_fragment_the_creative_profile_allows():
    rules = load_json("foundation.json")["absolute_rules"]["rules"]
    d = next(r for r in rules if r["id"] == "AR-003")["directive"]
    assert "fiction" in d and "scene breaks off" in d
    creative = load_json("content_profiles.json")["profiles"]["creative"]
    assert "scene breaks off" in creative["layer_adjustments"]["structural_patterns"]["notes"]


def test_non_uniformity_examples_name_moves_this_round_keeps():
    f = load_json("foundation.json")
    scope = f["enforcement"]["non_uniformity_scope"]
    assert "burstiness" not in scope and "hedging" not in scope
    caveat = next(
        c for c in load_json("caveats.json")["core_caveats"]
        if c["id"] == "uniform_application_paradox"
    )
    for word in ("fragment", "rhetorical question", "informal word", "burstiness"):
        assert word not in caveat["explanation"], word
    phase8 = next(p for p in f["application_protocol"]["phases"] if p["phase"] == 8)
    assert "fragment" not in phase8["stop_condition"]


def test_alternatives_do_not_lead_into_other_rules():
    alts = {t["term"]: t["alternatives"] for t in load_flagged_terms()}
    assert "Really" not in alts["At its core"]
    assert "Somewhat" not in alts["To some extent"]


def test_new_served_strings_ask_for_no_beats():
    for needle in ("Keep the friction the source has", "Let each section's texture"):
        for path, text in _strings_containing(needle):
            assert not asks_for_beats(text), path
