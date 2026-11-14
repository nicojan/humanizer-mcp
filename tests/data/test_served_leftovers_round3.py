"""Data-only cleanup round, 2026-11-13: served text that still asked the model
to perform a human trait, set a quota or a target, or gave an example that
invents facts or hardens or softens a claim (AR-001).

The substring removals sit in `REMOVED_PHRASES` in test_guide_consistency.py.
This module pins what a removal list cannot: shapes across every profile, a
quota pattern over all served text, and a before/after fact check on two
anti-pattern examples. See docs/RULE-HISTORY.md for the round index.
"""

import re

from src.storage.json_store import load_json
from tests.data.test_guide_consistency import served_texts

_LEVEL = re.compile(r"\b(?:low|moderate|high)\b", re.IGNORECASE)


def _profiles() -> dict:
    return load_json("content_profiles.json")["profiles"]


def _ap(ap_id: str) -> dict:
    return next(p for p in load_json("anti_patterns.json")["patterns"] if p["id"] == ap_id)


# ---------------------------------------------------------------------------
# Profile axis values say "not a target" and name no level
# ---------------------------------------------------------------------------


def test_every_profile_axis_value_says_it_is_not_a_target():
    profiles = _profiles()
    assert len(profiles) == 7
    for name, profile in profiles.items():
        for key in ("perplexity_target", "burstiness_target"):
            assert "not a target" in profile[key].lower(), (name, key, profile[key])
            assert len(profile[key]) <= 260, (name, key)


def test_no_profile_axis_value_names_a_level():
    for name, profile in _profiles().items():
        for key in ("perplexity_target", "burstiness_target"):
            assert not _LEVEL.search(profile[key]), (name, key, profile[key])


# ---------------------------------------------------------------------------
# No "at least one/two" quota anywhere in served text
# ---------------------------------------------------------------------------

_AT_LEAST = re.compile(
    r"\bat least (?:one|two|three)\b|\bno fewer than\b|\ba minimum of\b", re.IGNORECASE
)
# Every remaining use needs a one-line reason here. None remain after round 3.
AT_LEAST_ALLOWED: frozenset[str] = frozenset()


def test_at_least_control_pattern_fires():
    assert _AT_LEAST.search("rewrite at least one with a different construction")
    assert _AT_LEAST.search("keep at least three examples")
    assert _AT_LEAST.search("use no fewer than four items")
    assert _AT_LEAST.search("include a minimum of two quotes")
    assert not _AT_LEAST.search("at least a week")


def test_no_served_string_sets_an_at_least_quota():
    bad = [p for p, s in served_texts() if _AT_LEAST.search(s) and p not in AT_LEAST_ALLOWED]
    assert bad == []


# ---------------------------------------------------------------------------
# AP-020 and AP-027: the after adds nothing the before lacks
# ---------------------------------------------------------------------------

_PRONOUNS = frozenset({"i", "we", "my", "our", "me", "us", "i'm", "we're", "i've", "we've"})
_STOP = frozenset(
    "a an and as at be by for from in into is it its of on or that the their them "
    "they this to was with which who where while than then so both each can are up".split()
)


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'’-]*", text)


def invented_terms(before: str, after: str) -> set[str]:
    """Capitalized words (a sentence-start word counts) and first-person
    pronouns in `after` that are absent from `before`, minus plain function
    words."""
    before_words = {w.lower() for w in _words(before)}
    out: set[str] = set()
    for token in _words(after):
        low = token.lower()
        if low in before_words or low in _STOP:
            continue
        if token[0].isupper() or low in _PRONOUNS:
            out.add(low)
    return out


def unsupported_words(before: str, after: str, allow: frozenset[str] = frozenset()) -> set[str]:
    """Content words of `after` (lowercased, minus function words and the
    explicit `allow` set) with no match in `before`. A match is a shared
    prefix of up to five letters, so simple inflection passes."""
    pool = [w.lower() for w in _words(before) if len(w) >= 3]
    out: set[str] = set()
    for token in _words(after):
        low = token.lower()
        if low in _STOP or low in allow:
            continue
        if not any(low[: min(5, len(low), len(p))] == p[: min(5, len(low), len(p))] for p in pool):
            out.add(low)
    return out


# Per example, the connective words the rewrite needs that the before lacks.
# Each entry is a plain restatement word, never a fact, name or judgment.
_ALLOWED = {
    "AP-020": frozenset({"get", "along", "well"}),
    "AP-027": frozenset({"finished", "used", "well", "worked"}),
    "AP-011": frozenset({"along", "well"}),
    "AP-005": frozenset(),
}


def test_invented_terms_control_catches_names_pronouns_and_judgment():
    before = "The project was completed on schedule."
    assert "teodora" in invented_terms(before, "Teodora ran the standups.")
    assert "teodora" in invented_terms(before, "We shipped. Then Teodora ran standups.")
    assert {"we", "we're"} <= invented_terms(before, "We shipped. We're done.")
    assert "useful" in invented_terms(before, "Useful for teams.")
    assert invented_terms(before, "The project was completed on schedule.") == set()


def test_unsupported_words_control_catches_a_new_word_and_passes_inflection():
    before = "The platform provides data analytics and integration with CRM systems."
    assert unsupported_words(before, "The platform integrates CRM system data.") == set()
    assert "patience" in unsupported_words(before, "The platform takes patience.")
    assert "fast" in unsupported_words(before, "Analytics run fast.")
    assert unsupported_words(before, "Analytics run fast.", frozenset({"run", "fast"})) == set()


def test_rewrites_add_no_word_the_before_lacks():
    for ap_id, allow in _ALLOWED.items():
        ap = _ap(ap_id)
        assert unsupported_words(ap["before"], ap["after"], allow) == set(), (ap_id, ap["after"])
        assert invented_terms(ap["before"], ap["after"]) == set(), (ap_id, ap["after"])


def test_ap020_after_adds_no_name_pronoun_or_judgment():
    ap = _ap("AP-020")
    for old in ("react fast", "most CRM", "patience", "useful for teams"):
        assert old not in ap["after"], old
    for old in ("of unequal length", "known facts about it", "evaluative"):
        assert old not in ap["explanation"], old
    assert "absolute_rules AR-001" in ap["explanation"]


def test_ap020_after_keeps_every_item_of_the_before():
    ap = _ap("AP-020")
    after = ap["after"].lower()
    for item in ("analytics", "real-time reporting", "automated alerts", "crm", "email",
                 "project management", "dashboards", "exportable reports", "role-based access"):
        assert item in after, item


def test_ap020_after_folds_three_lists_into_fewer_sentences():
    ap = _ap("AP-020")
    count = lambda t: len(re.findall(r"[.!?](?:\s|$)", t))
    assert count(ap["after"]) < count(ap["before"])


def test_ap027_after_keeps_the_claim_strength_and_names_nothing():
    ap = _ap("AP-027")
    for old in ("Teodora", "authentication", "exhausted", "standups"):
        assert old not in ap["after"], old
    assert "manage its work well" in ap["after"]
    assert "key milestones" in ap["after"]
    assert "worked stakeholder feedback in" in ap["after"]


def test_ap027_explanation_ties_specifics_to_the_source_notes():
    text = _ap("AP-027")["explanation"].lower()
    assert "source notes" in text
    assert "name" in text and "bug" in text
    assert "first-person perspective introduced" not in text


def test_ap011_after_keeps_all_six_items_and_two_non_parallel_sentences():
    after = _ap("AP-011")["after"].lower()
    for item in ("seo professionals", "marketing experts", "growth hackers", "keynote sessions",
                 "panel discussions", "networking opportunities", "latest trends in digital marketing"):
        assert item in after, item
    assert "strategies" not in after and "talks" not in after


def test_ap005_after_states_both_facts_and_adds_no_closer():
    ap = _ap("AP-005")
    after = ap["after"]
    assert "paint on paper" in after and "gave up on the polished apps" in after
    assert "handmade" not in after and "because it is" not in after
    assert "short, confident close" not in ap["explanation"]


# ---------------------------------------------------------------------------
# Cohesive devices: no question opener, no loose-reference praise
# ---------------------------------------------------------------------------


def test_paragraph_opening_guidance_no_longer_offers_a_question():
    rules = load_json("discourse_cohesion.json")["cohesive_devices"]["rules"]
    assert "a question" not in rules[2]["guidance"]
    assert "question" not in rules[2]["guidance"].lower()


def test_pronoun_rule_asks_for_a_clear_referent():
    rules = load_json("discourse_cohesion.json")["cohesive_devices"]["rules"]
    assert "clear referent" in rules[1]["rule"]
    assert "ambigu" not in load_json("discourse_cohesion.json")["cohesive_devices"]["human_pattern"].lower()


def test_comparison_rule_keeps_only_the_sources_comparisons():
    rule = load_json("discourse_cohesion.json")["cohesive_devices"]["rules"][3]
    assert "AR-001" in rule["guidance"]
    assert "source" in rule["rule"].lower()


# ---------------------------------------------------------------------------
# Condition on the source, never on a performance
# ---------------------------------------------------------------------------


def test_emotional_layering_rules_keep_the_sources_strength_and_mix():
    rules = load_json("sentiment_tone.json")["emotional_layering"]["rules"]
    assert "source" in rules[0]["rule"].lower() and "strength" in rules[0]["rule"]
    assert "source" in rules[1]["rule"].lower()
    assert "AR-001" in rules[1]["guidance"]
    assert "human" not in rules[4]["guidance"].lower()


def test_negative_judgment_example_keeps_its_strength():
    rule = load_json("sentiment_tone.json")["neutral_bias"]["rules"][1]
    assert "strength" in rule["rule"]
    assert "some problems worth looking at" in rule["guidance"]


def test_enumeration_examples_add_no_fact():
    rules = load_json("structural_patterns.json")["enumeration_patterns"]["rules"]
    blob = " ".join(r["guidance"] for r in rules)
    assert "client presentations" not in blob
    assert "took most of the time" not in blob
    assert "AR-001" in blob or "source" in blob


def test_contractions_follow_register_and_source_with_no_quota():
    g = load_json("lexical_patterns.json")["word_length_patterns"]["rewriting_guidance"]
    assert "source" in g[2].lower()
    assert "Some sentences with" not in g[2]


# ---------------------------------------------------------------------------
# Fix wave: irregularity targets, plain links, source-conditioned markers
# ---------------------------------------------------------------------------

_NO_TARGET = "a paragraph without one stays as written"


def test_no_served_text_targets_an_irregular_distribution_of_edits():
    f = load_json("foundation.json")
    core = f["core_principle"]["explanation"]
    assert "where the register and the source call for them" in core
    assert "applied selectively and unevenly" in core  # the principle stays
    directive = f["application_protocol"]["uniformity_directive"]
    caveat = next(
        c for c in load_json("caveats.json")["core_caveats"]
        if c["id"] == "uniform_application_paradox"
    )["explanation"]
    for text in (directive, caveat):
        assert "Edit where the draft has a tell" in text and _NO_TARGET in text
        assert "irregular" not in text.lower()
    assert "Apply rules unevenly" in caveat


def test_transition_guidance_names_the_plain_word_for_each_stated_relation():
    rule = load_json("discourse_cohesion.json")["discourse_markers"]["rules"][2]
    g = rule["guidance"]
    assert "'And' or 'Also' for an addition" in g
    assert "'So' for a result" in g and "'But' for a contrast" in g
    assert "the relation the source states" in g


def test_paragraph_opening_rule_header_asks_for_no_variety():
    rule = load_json("discourse_cohesion.json")["cohesive_devices"]["rules"][2]
    assert rule["rule"] == "Open a paragraph on what it carries."
    assert "question" not in rule["guidance"].lower()


def test_enumeration_examples_rank_nothing_and_match_the_new_wording():
    sp = load_json("structural_patterns.json")["enumeration_patterns"]
    rules = sp["rules"]
    assert "'The report exports to CSV and PDF.'" in rules[0]["guidance"]
    assert "before deploying it, which was the hardest part" in rules[2]["guidance"]
    assert "dashboards present both" in rules[1]["guidance"]
    hp = sp["human_pattern"]
    assert "list as many items as there are" in hp and "two-item" not in hp
    ngram = load_json("structural_patterns.json")["n_gram_patterns"]["rewriting_guidance"][1]
    assert "repeat by habit" in ngram and "keep a repeat the content needs" in ngram


def test_bs009_fix_matches_the_wording_the_checker_serves():
    from src.checker import run_checks

    served = next(
        f["fix"]
        for f in run_checks("This is slow. This costs money. This hurts users.")["must_clear"]
        if f.get("id") == "BS-009"
    )
    data = next(s for s in load_json("banned_structures.json")["structures"] if s["id"] == "BS-009")
    assert data["fix"] == served


def test_surface_pattern_guidance_sets_no_evenness_or_human_comparison():
    pt = load_json("psycholinguistic_texture.json")
    assert "human" not in pt["cognitive_load_artifacts"]["rewriting_guidance"][2].lower()
    sv = load_json("structural_patterns.json")["syntactic_variety"]["rules"][2]["guidance"]
    assert "Keep the passives the source uses" in sv and "no ratio" in sv
    assert "lengths and openings differ" not in _ap("AP-021")["explanation"]
    assert "Lengths and openings follow the content" in _ap("AP-021")["explanation"]
    assert "as long as its points need" in _ap("AP-026")["explanation"]


def test_human_markers_that_perform_a_trait_belong_to_the_source():
    pt = load_json("psycholinguistic_texture.json")
    hm = pt["self_monitoring_traces"]["human_markers"] + pt["lexical_retrieval_signatures"]["human_markers"] \
        + pt["discourse_planning_traces"]["human_markers"]
    watched = [m for m in hm if re.search(r"tone shifts|informal or colloquial|topic shifts|^Contractions", m, re.I)]
    assert len(watched) == 4, watched
    for m in watched:
        assert "source" in m.lower(), m


def test_concrete_noun_guidance_is_conditioned_on_the_source():
    ac = load_json("lexical_patterns.json")["abstract_concrete_balance"]
    assert "if the notes say" in ac["human_pattern"].lower()
    assert "the ones the source names" in ac["rules"][0]["guidance"]
    assert "absolute_rules AR-001" in ac["rules"][1]["guidance"]
    vd = load_json("lexical_patterns.json")["vocabulary_diversity"]["rewriting_guidance"][1]
    assert vd.count("the source names") == 2


def test_profile_notes_follow_the_draft_and_the_source():
    p = _profiles()
    assert p["technical"]["special_considerations"][1].startswith("Keep the warnings, edge cases and known issues the source or the user gives")
    assert "absolute_rules AR-001" in p["technical"]["special_considerations"][1]
    academic = p["academic"]
    assert academic["special_considerations"][2].startswith("Keep the position the author takes visible")
    assert "depth that follows the evidence" in academic["layer_adjustments"]["psycholinguistic_texture"]["notes"]
    marketing = p["marketing"]["special_considerations"]
    assert marketing[1].startswith("Write from what the brief and the source say about the product")
    assert marketing[2].endswith("Present each benefit the way its content needs.")
    creative = p["creative"]["layer_adjustments"]
    assert "Keep the mixed feelings the draft gives a moment." in creative["sentiment_tone"]["notes"]
    assert "She slammed the drawer shut" in creative["sentiment_tone"]["notes"]
    assert "each moment getting the length it needs" in creative["structural_patterns"]["notes"]
    assert "The voice comes from the draft and the narrator" in creative["psycholinguistic_texture"]["notes"]
    assert "most precise vocabulary" in creative["lexical_patterns"]["notes"]
    general = p["general_prose"]["layer_adjustments"]["sentiment_tone"]["notes"]
    assert general.startswith("Let the opinions, evaluations and recommendations")


def test_personal_stance_rule_supplies_none():
    rule = load_json("sentiment_tone.json")["emotional_layering"]["rules"][3]
    assert rule["rule"] == "Keep the stance the user or the source holds."
    assert "supply none (absolute_rules AR-001)" in rule["guidance"]


def test_case_study_ux_note_names_the_source_decision_without_a_ranking_line():
    note = _profiles()["case_study"]["special_considerations"][1]
    assert note.startswith("Make the UX decision the source names as the main one land")
    assert "beats five" not in note
