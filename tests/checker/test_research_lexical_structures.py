"""Groups A + B: research-backed lexical additions and discourse banned_structures,
verified end-to-end through run_checks. Lexical words and regex structures are
auto-wired via the loader, so these are integration tests over the live data.

Sources: Kobak et al. (Science Advances 2025) — 'underscore' r=13.8; Juzek & Ward
(COLING 2025) — 'surpass'; the negation-flip antithesis ("it's not X, it's Y") is
the single most characteristic rhetorical tell of LLM prose (Dead Language Society
rhetorical analysis, 2025)."""

from src.checker import run_checks

# --- Group A: lexical additions (underscore / surpass / boast) ---------------


def test_underscore_verb_surfaces_as_must_clear():
    r = run_checks(
        "The results matter. This finding underscores the gap we measured.",
        "prose",
    )
    assert any(m.get("term") == "underscore" for m in r["must_clear"])


def test_surpass_surfaces_as_must_clear():
    r = run_checks(
        "Our revenue grew last year. It surpassed every forecast we had set.",
        "prose",
    )
    assert any(m.get("term") == "surpass" for m in r["must_clear"])


def test_boast_surfaces_as_must_clear():
    """Now BS-049 rather than a bare lexicon term: the word was scoped to its
    collocation on 2026-09-18 after measuring 7.4 per 10k on human prose, where
    'boast' is an ordinary verb of vanity. The tell is 'boasts a/an/over X'."""
    r = run_checks(
        "The new campus is large. It boasts three libraries and a quiet garden.",
        "prose",
    )
    assert any(m.get("id") == "BS-049" for m in r["must_clear"])


def test_bare_boast_is_no_longer_flagged():
    r = run_checks("He was not a man to boast of his own courage.", "prose")
    assert not any(m.get("id") == "BS-049" for m in r["must_clear"])
    assert not any(m.get("term") == "boast" for m in r["must_clear"])


# --- Group B: discourse banned_structures (checklist gate, never hard) --------


def test_negation_flip_antithesis_surfaces_as_must_clear_not_hard():
    r = run_checks(
        "The studio is not five machines. It is one path a student follows.",
        "prose",
    )
    assert any(m.get("name") == "negation_flip_antithesis" for m in r["must_clear"])
    assert not any(
        v.get("type") == "banned_structure" for v in r["hard_violations"]
    )


def test_rarely_flip_aphorism_surfaces_as_must_clear():
    r = run_checks(
        "The hard part is rarely the new tool. It is deciding what to leave alone.",
        "prose",
    )
    assert any(m.get("name") == "rarely_flip_aphorism" for m in r["must_clear"])


def test_wh_cleft_pronouncement_surfaces_as_must_clear():
    r = run_checks("What matters here is the design itself.", "prose")
    assert any(m.get("name") == "wh_cleft_pronouncement" for m in r["must_clear"])


def test_meta_framing_opener_surfaces_as_must_clear():
    r = run_checks(
        "The point of the redesign is the gap between the two shapes.",
        "prose",
    )
    assert any(m.get("name") == "meta_framing_opener" for m in r["must_clear"])


# --- Group B: false-positive guards -------------------------------------------


def test_clean_two_sentence_prose_triggers_no_new_structure():
    r = run_checks("We shipped on Tuesday. The team was tired but proud.", "prose")
    names = {m.get("name") for m in r["must_clear"]}
    assert "negation_flip_antithesis" not in names
    assert "wh_cleft_pronouncement" not in names
    assert "meta_framing_opener" not in names


def test_wh_question_is_not_a_wh_cleft():
    # A genuine interrogative ends in '?', not '.', and must not trip the cleft.
    r = run_checks("What is the plan for next quarter?", "prose")
    assert not any(
        m.get("name") == "wh_cleft_pronouncement" for m in r["must_clear"]
    )


def test_negation_flip_skips_participial_state_denial():
    # "is not signed yet. It was sent" denies a STATE, not a noun-phrase
    # identity. It is ordinary prose, not the AI antithesis, and must not fire.
    r = run_checks(
        "The contract is not signed yet. It was sent to them last week.", "prose"
    )
    assert not any(
        m.get("name") == "negation_flip_antithesis" for m in r["must_clear"]
    )


def test_negation_flip_skips_adjectival_state_denial():
    r = run_checks("The build is not ready. It is still running.", "prose")
    assert not any(
        m.get("name") == "negation_flip_antithesis" for m in r["must_clear"]
    )


def test_wh_cleft_skips_fused_relative_with_subject():
    # "What I learned was invaluable" is a fused relative clause (What = object
    # of 'learned'), not a pseudo-cleft pronouncement. Must not fire.
    r = run_checks("What I learned was invaluable to me that year.", "prose")
    assert not any(
        m.get("name") == "wh_cleft_pronouncement" for m in r["must_clear"]
    )
