"""Served-text leftovers swept in the repair round's Task 11, part B.

Each test pins one routed item: a target or a performance the guidance still
asked for, an AR-001 contradiction (a rewrite that adds a fact, softens or
hardens), a tell word in a fix text, or a wording error. The removals sit in
`REMOVED_PHRASES` in test_guide_consistency.py; this module pins what a
removal list cannot.
"""

import json
import re

from src.storage.json_store import load_json
from tests.checker.test_rubric import outside_quotes
from tests.data.test_guide_consistency import fires, served_texts


def _phase(n: int) -> dict:
    phases = load_json("foundation.json")["application_protocol"]["phases"]
    return next(p for p in phases if p["phase"] == n)


def _profile(name: str) -> dict:
    return load_json("content_profiles.json")["profiles"][name]


def _ap(ap_id: str) -> dict:
    return next(p for p in load_json("anti_patterns.json")["patterns"] if p["id"] == ap_id)


# ---------------------------------------------------------------------------
# Items 1-7: describe, never target; condition on the source
# ---------------------------------------------------------------------------


def test_section_types_describe_texture_without_axis_targets():
    section = load_json("structural_patterns.json")["cross_segment_variation"]
    text = json.dumps(section["section_types"]).lower()
    assert section["section_types"], "section types must be served"
    assert "burstiness" not in text and "perplexity" not in text


def test_perplexity_is_described_with_a_plain_example():
    axes = load_json("foundation.json")["two_axes"]["perplexity"]
    assert "The numbers don't lie" not in axes["high"]
    assert _profile("creative")["perplexity_target"] != "high"


def test_durable_signal_item_asks_for_no_surprising_words():
    from src.checker.loader import load_self_review

    item = next(i for i in load_self_review() if i["id"] == "durable_signal")
    assert "unpredictab" not in item["detail"].lower()


def test_phase_5_sets_no_axis_targets():
    purpose = _phase(5)["purpose"].lower()
    assert "perplexity" not in purpose and "burstiness" not in purpose


def test_phase_2_varies_syntax_and_punctuation_only_on_a_condition():
    phase = _phase(2)
    text = f"{phase['purpose']} {phase['stop_condition']}"
    assert "vary syntactic construction and punctuation" not in text
    assert "syntactic variety is introduced" not in text
    assert "punctuation choice varies across sections" not in text
    assert "for its own sake" in phase["stop_condition"]
    meta = load_json("structural_patterns.json")["meta"]["description"]
    assert "varying syntactic construction and punctuation" not in meta


_FULL = re.compile(r"""rubric=["']full["']""")


def test_plainness_pass_runs_before_the_final_full_check_and_ends_with_a_check():
    p9, p10 = _phase(9), _phase(10)
    assert "Runs last" not in p10["purpose"]
    assert _FULL.search(p10["purpose"]) and "before" in p10["purpose"]
    assert "prohibitions_clear" in p10["stop_condition"]
    assert _FULL.search(p10["stop_condition"])
    assert "phase 10" in p9["stop_condition"].lower()
    orwell = load_json("lexical_patterns.json")["orwell"]["description"]
    assert "runs LAST" not in orwell


_PLAINNESS_LAST = re.compile(r"\b(?:pass|runs?)\s+last\b|\blast pass\b", re.IGNORECASE)
_PLAINNESS_TOPIC = re.compile(r"orwell|plainness|stale figures?", re.IGNORECASE)


def puts_plainness_last(text: str) -> bool:
    """True when a string about the plainness pass says it runs last."""
    return bool(_PLAINNESS_TOPIC.search(text) and _PLAINNESS_LAST.search(text))


def test_plainness_last_control():
    assert puts_plainness_last("Run this pass last (the Orwell pass), after the other phases.")
    assert puts_plainness_last("As the last pass, read once more for stale figures.")
    assert puts_plainness_last("The Orwell pass runs LAST, on cleared copy.")
    assert not puts_plainness_last("The Orwell pass runs before the final check.")
    assert not puts_plainness_last("Run this pass last.")  # not about plainness


def test_no_served_string_puts_the_plainness_pass_last():
    bad = [path for path, text in served_texts() if puts_plainness_last(text)]
    assert bad == []


def test_plainness_rubric_item_matches_phase_10():
    from src.checker.loader import load_self_review

    item = next(i for i in load_self_review() if i["id"] == "plainness")
    assert len(item["short"]) <= 200 and item["short"][-1] in ".!?"
    for text in (item["short"], item["detail"]):
        assert _FULL.search(text) and "before" in text.lower(), text
        assert "prohibitions_clear" in text, text
    guidance = load_json("lexical_patterns.json")["orwell"]["rewriting_guidance"][0]
    assert _FULL.search(guidance) and "prohibitions_clear" in guidance


def test_general_prose_adds_no_conversational_bridge():
    notes = _profile("general_prose")["layer_adjustments"]["discourse_cohesion"]["notes"]
    assert "conversational bridges where appropriate" not in notes
    assert "source" in notes


def test_stance_and_register_asks_are_conditioned_on_the_source():
    academic = _profile("academic")["layer_adjustments"]
    marketing = _profile("marketing")["layer_adjustments"]
    assert "Reintroduce evaluative language" not in academic["sentiment_tone"]["notes"]
    assert "source" in academic["sentiment_tone"]["notes"]
    assert "occasional evaluative language" not in academic["psycholinguistic_texture"]["notes"]
    assert "vary the emotional register" not in marketing["sentiment_tone"]["notes"]
    assert re.search(r"\b(?:source|brief|user)\b", marketing["sentiment_tone"]["notes"])
    modal = load_json("discourse_cohesion.json")["modal_and_epistemic_markers"]["human_pattern"]
    assert "distribute these unevenly" not in modal
    assert "source" in modal


# ---------------------------------------------------------------------------
# Items 8-11: AR-001 contradictions
# ---------------------------------------------------------------------------


def test_adverb_rules_add_no_manner_and_no_qualification():
    adverbs = load_json("lexical_patterns.json")["adverb_patterns"]
    blob = json.dumps(adverbs["rules"])
    assert "'The team responded' →" not in blob
    assert "Distribute adverbs unevenly" not in blob
    assert "adverb-dense" not in blob
    for rule in adverbs["rules"]:
        assert "source" in rule["guidance"], rule["rule"]
    assert "Reintroducing them" not in adverbs["description"]


def test_arguably_offers_no_hardened_claim():
    items = load_json("lexical_patterns.json")["flagged_qualifiers"]["items"]
    alts = next(i for i in items if i["ai_phrase"] == "Arguably")["alternatives"]
    assert not any("direct claim" in a for a in alts), alts


def test_ap052_after_keeps_the_source_strength():
    after = _ap("AP-052")["after"]
    assert "the only point" not in after
    assert "a design can reach the officer" in after
    assert fires(after) == []


def test_copula_rule_sets_no_quota():
    rules = load_json("structural_patterns.json")["syntactic_variety"]["rules"]
    copula = next(r for r in rules if r["rule"].startswith("Reduce copula"))
    assert "at least one needs restructuring" not in copula["guidance"]
    assert "at least one" not in copula["guidance"]


# ---------------------------------------------------------------------------
# Item 12: tell words in served fix texts
# ---------------------------------------------------------------------------

_FIX_TELLS = re.compile(
    r"\b(?:actually|actual|genuinely|genuine|real|really|quietly|honestly)\b|\bnot because\b",
    re.IGNORECASE,
)


def fix_tells(text: str) -> list[str]:
    """Tell words in a fix text, outside the bad forms it quotes."""
    return _FIX_TELLS.findall(outside_quotes(text))


def test_fix_tell_control():
    assert fix_tells("Say what actually happened.") == ["actually"]
    assert fix_tells("If the trade-off is real, name it.") == ["real"]
    assert fix_tells("Not because X, but because Y.") == ["Not because"]
    assert fix_tells("Cut 'Quietly reshaping the industry' and name the change.") == []
    assert fix_tells("Name the cost and who pays it.") == []


def test_banned_structure_fix_texts_carry_no_tell_words():
    structures = load_json("banned_structures.json")["structures"]
    assert len(structures) > 50
    bad = {s["id"]: fix_tells(s["fix"]) for s in structures if fix_tells(s.get("fix", ""))}
    assert bad == {}


# ---------------------------------------------------------------------------
# Items 14-19: grammar, accuracy, wording
# ---------------------------------------------------------------------------


def test_resume_note_reads_as_sentences():
    note = _profile("resume")["special_considerations"][0]
    assert "and and" not in note


def test_ap035_explanation_gives_the_flourish_a_verb():
    explanation = _ap("AP-035")["explanation"]
    assert "A self-aware flourish that performs concision" not in explanation


def test_bs066_description_scopes_to_what_the_pattern_counts():
    bs066 = next(
        s for s in load_json("banned_structures.json")["structures"] if s["id"] == "BS-066"
    )
    assert "every form" not in bs066["description"].lower()
    assert "contracted and uncontracted" in bs066["description"]


def test_ar003_scene_break_fragment_covers_narrative():
    rules = load_json("foundation.json")["absolute_rules"]["rules"]
    ar003 = next(r for r in rules if r["id"] == "AR-003")["directive"]
    assert "in fiction marks" not in ar003
    assert "in narrative" in ar003


def test_marketing_lexical_note_gives_a_positive_instruction():
    notes = _profile("marketing")["layer_adjustments"]["lexical_patterns"]["notes"]
    assert "not 'innovative technology' but" not in notes
    assert "'innovative technology'" in notes


# ---------------------------------------------------------------------------
# Item 20: docs that paraphrase served text
# ---------------------------------------------------------------------------


def _doc(name: str) -> str:
    import pathlib

    return (pathlib.Path(__file__).resolve().parents[2] / "docs" / name).read_text()


def test_docs_follow_the_served_wording():
    assert "judgment, not prohibition" not in _doc("DATA_SCHEMA.md")
    assert "fix and re-run until `prohibitions_clear`" not in _doc("API_SPEC.md")
    # docs/RULE-HISTORY.md is private-only; the public export does not carry it.
    import pathlib

    history = pathlib.Path(__file__).resolve().parents[2] / "docs" / "RULE-HISTORY.md"
    if history.exists():
        text = history.read_text()
        assert "GUARD_WITNESSES` holds 79" not in text
        assert "are gone. Guidance that hardened" not in text


def test_served_texts_still_found():
    """Control: the served walk above is not empty."""
    assert len(served_texts()) > 1000
